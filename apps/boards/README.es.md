# boards

## Descripción

Biblioteca personal por usuario. Organiza recursos en **tableros** (boards) mostrados como un
mosaico (carpetas, archivos, enlaces, grabaciones de voz y páginas impulsadas por el motor de
landing). Permite compartir enlaces, guardar el tablero de otro usuario en solo lectura, colaborar
con otros usuarios y duplicar elementos según la configuración del propietario.

Relación con las apps núcleo:

- **`user_levels`** — límites de creación (`BOARDS_MODEL_KEY`) y rutas restringidas. Toda decisión
  de ACL en `services/board_permissions.py` termina llamando a `check_action_allowed` o
  `get_visible_creator_ids`; boards nunca reimplementa las reglas de nivel.
- **`core`** — `BaseForm`, procesamiento de archivos (`process_image_field_if_changed`), wrappers de
  Redis, miniaturas PDF, URLs de vista previa al compartir y el contrato HTMX
  `attach_toast_trigger` / `htmx_error_response`.
- **`users.User`** — propietario de `Board`, `BoardCollaborator` y `BoardLibraryEntry`.
- **`landing`** — los elementos de tipo `page` crean y renderizan un `LandingPage` con
  `page_context=board`.
- **`keyboard_api`** — las mutaciones de tablero encolan tareas Celery que envían notificaciones FCM
  silenciosas al cliente del teclado móvil.

## Modelos y datos

| Modelo | Responsabilidad |
|---|---|
| `Board` | Contenedor del usuario: título, imagen de portada, orden, `share_token`, `allow_duplicate_on_share`, `is_public`. FK → `users.User` |
| `BoardFolder` | Carpetas anidables (`parent` FK → self), ordenables en el mosaico |
| `BoardItem` | Elemento del mosaico. Tipos: `text`, `image`, `link`, `video`, `voice`, `pdf`, `youtube`, `page`. Archivos hasta 10 MB. FK opcional → `landing.LandingPage` |
| `BoardCollaborator` | Usuario invitado con acceso de lectura y edición. Único en `(board, user)` |
| `BoardLibraryEntry` | Referencia a un tablero compartido guardado en la biblioteca propia (solo lectura) |
| `BoardDeleteLog` | Registro append-only de tableros eliminados de forma permanente. `board_id` / `user_id` son enteros simples porque la fila `Board` ya no existe. Lo consume **solo** el endpoint de delta-sync de la keyboard API para que los clientes móviles sepan qué purgar |

### Lógica de acceso

| Tipo de usuario | Ver | Editar | Gestionar | Duplicar |
|---|---|---|---|---|
| Propietario | ✓ | ✓ | ✓ | ✓ |
| Colaborador | ✓ | ✓ | — | ✓ |
| Entrada de biblioteca | ✓ | — | — | Solo si `allow_duplicate_on_share` |
| Tablero público | ✓ | — | — | — |

### Permisos según el plan

| Nivel | Acceso | Límite de creación | Compartir con el equipo (`is_public`) |
|---|---|---|---|
| Basic | Leer públicos/compartidos; escribir solo como colaborador | — | — |
| Pro | Sí | 1 | — |
| Leader | Sí | 3 | Sí, dentro de su burbuja de visibilidad |
| Leader Pro | Sí | Ilimitado | Sí, mismas reglas de burbuja |

Las rutas restringidas devuelven 404 a través de `RouteLevelAccessMiddleware`. Los colaboradores de
nivel Basic conservan acceso de escritura en los tableros en los que colaboran.

### Servicios

| Módulo | Función |
|---|---|
| `services/board_permissions.py` | ACL: propiedad, colaboración, visibilidad pública, duplicación, visibilidad por nivel |
| `services/board_collaborators.py` | `add_collaborator` / `remove_collaborator` con validación e invalidación de caché |
| `services/board_items.py` | Creación de elementos tipo `page` (genera un `LandingPage`) y duplicación recursiva de elementos con archivos |
| `services/board_cache.py` | Caché Redis del payload del mosaico por tablero y carpeta (TTL 300 s) |
| `services/search_index.py` | Índice de búsqueda Redis por usuario sobre tableros propios, colaborados, guardados y públicos |
| `services/bulk_operations.py` | Borrado, traslado y duplicación masivos con soporte de árbol de carpetas |
| `services/mosaic_preview.py` | Genera y sincroniza miniaturas WebP de azulejos, incluidas previews de la primera página de PDF |
| `services/landing_page_preview.py` | Resuelve URLs de preview y HTML embebido para elementos tipo `page` |
| `services/board_cover.py` | Reprocesa la portada del tablero a WebP |
| `services/item_titles.py` | Resuelve títulos de elementos desde fuentes externas (YouTube, metadatos de enlace) |
| `services/voice_convert.py` | WebM → MP3 mediante ffmpeg; lanza `VoiceConversionError` |
| `services/folder_options.py` | Opciones de carpeta para el desplegable legacy del modal de mover; el selector de destino carga carpetas bajo demanda desde el endpoint JSON del mosaico |
| `services/keyboard_sync.py` | Actualiza `updated_at` y encola la tarea Celery de sync móvil |
| `utils.py` | Resolución de acceso al tablero, payload del mosaico, reordenación, contexto de detalle |
| `link_meta.py`, `youtube.py` | Peticiones salientes para previews Open Graph y oEmbed de YouTube |

## Vistas e integración frontend

**Esta app usa HTMX**, pero solo para el envío de formularios: el mosaico en sí sigue siendo una
rejilla Muuri del lado del cliente alimentada por JSON.

Prefijo de URL: **`/boards/`**

### Endpoints HTMX

| Endpoint | Name | Comportamiento HTMX |
|---|---|---|
| `<id>/item/form/` | `load_board_item_form` | GET parcial → `components/partials/board-item-form-fields.html` |
| `save/` | `save_board` | `204` + **`HX-Redirect`** al tablero nuevo |
| `<id>/folder/save/` | `save_board_folder` | Toast `HX-Trigger` vía `attach_toast_trigger` |
| `<id>/item/save/` | `save_board_item` | Toast `HX-Trigger`; `hx-encoding="multipart/form-data"` |
| `<id>/settings/` | `save_board_settings` | Toast `HX-Trigger` |
| `<id>/page/<landing_id>/preview/` | `board_landing_page_preview` | Fragmento HTML crudo para la preview embebida de landing |

Los fallos de validación devuelven `htmx_error_response` (422 + `HX-Trigger`). Plantillas de envío:
`components/modal-board.html`, `modal-board-folder.html`, `modal-board-item.html`,
`modal-board-settings.html`, todas con `hx-post` + `hx-swap="none"` y `data-close-modal`.

### Endpoints JSON y HTML

| Ruta | Name | Descripción |
|---|---|---|
| `""` | `boards_home` | Listado: tableros propios, colaborados, públicos y de biblioteca |
| `<id>/` · `<id>/folder/<folder_id>/` | `board_detail`, `board_folder` | Vista del mosaico |
| `<id>/mosaic/` | `board_mosaic_data` | Payload JSON de azulejos (cacheado en Redis) |
| `<id>/item/<item_id>/tile/` | `board_item_tile` | JSON de un azulejo tras editarlo |
| `<id>/item/<item_id>/file/` | `board_item_file` | Sirve el archivo con cabecera `inline` |
| `<id>/item/delete/` · `move/` · `duplicate/` | `delete_board_item`, `move_board_item`, `duplicate_board_item` | Mutaciones de elementos (JSON) |
| `<id>/folder/delete/` | `delete_board_folder` | Borrar carpeta (JSON) |
| `<id>/bulk/delete/` · `move/` · `duplicate/` | `bulk_*_board` | Operaciones de selección masiva (JSON) |
| `<id>/reorder/` | `reorder_board_mosaic` | Ordenación masiva de azulejos (JSON) |
| `<id>/collaborators/add/` · `remove/` | `add_board_collaborator`, `remove_board_collaborator` | Gestión de colaboradores (JSON) |
| `delete/` | `delete_board` | Borrar tablero (JSON); escribe una fila `BoardDeleteLog` |
| `search-index/` | `board_search_index` | Índice de búsqueda por usuario (JSON) |
| `link-meta/`, `youtube-meta/` | `board_link_meta`, `board_youtube_meta` | Consultas de metadatos salientes (JSON) |
| `share/<token>/` · `folder/<id>/` | `board_share`, `board_share_folder` | Vista compartida (requiere login) |
| `share/<token>/save/` | `save_shared_board` | Guardar en la biblioteca propia |
| `<username>/board_<id>/` | `board_page_template` | Página pública de un elemento tipo `page` |

### Notas de frontend

Las plantillas extienden `base-main.html`. El detalle del tablero muestra **Atrás** (carpeta padre o
raíz del tablero, solo dentro de una carpeta) y **Volver a Boards** en lugar de una ruta de
migas; ambos se ocultan en la vista de compartir.

Los toasts, el estado busy y el cierre de modales los gestiona el ciclo de vida HTMX global en
`static/js/core.js` reaccionando a `data-close-modal` y `HX-Trigger`. Los efectos secundarios
específicos de boards (recarga del mosaico, reindexación de búsqueda, redirección de elementos
page) permanecen en `board-detail.js` / `board-home.js`, enlazados a `htmx:afterRequest`.

El modal de elemento reutiliza el shell compartido `#formBoardItem-fields` +
`#formBoardItem-fields-template` cableado mediante kwargs `htmx_modal_*` en `base-modal.html`. El
HTML de los campos lo obtiene el cargador global `static/js/htmx_modal_form.js` desde
`load_board_item_form` (`item_id` al editar; la creación pasa `item_type` más un id centinela para
que el loader haga un GET en lugar de restaurar la plantilla vacía). `BoardItemForm` define los
campos visibles y el `accept` por tipo; la edición de PDF prioriza el `mosaic_preview` almacenado.
Tras el settle, el evento `boards:item-form-loaded` permite que `item-modal.js` enlace solo la UX de
dominio — previews al blur de YouTube/enlace, ayuda de nombre de archivo PDF, grabadora de voz. Las
previews de archivo vienen de `fileUploadUtils.initPreviewsInScope`, no se reimplementan aquí.

JS modular en `static/js/`: `api`, `mosaic`, `item-modal`, `item-viewer`, `board-detail`,
`board-home`, `board-search`, `board_destination_picker`, `voice-recorder`, `pdf-preview`. Estilos en
`static/css/boards.css`, que importa `boards-search`, `boards-tiles`, `boards-mosaic` y
`boards-viewer`.

## Configuración y dependencias

| Setting | Propósito |
|---|---|
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Caché del mosaico e índice de búsqueda por usuario |
| `FFMPEG`, `FFPROBE` | Conversión de grabaciones de voz (WebM → MP3) |
| `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE` | Subidas de elementos (tope de 10 MB aplicado en el modelo) |
| `R2_*` | Archivos de elementos y portadas van a Cloudflare R2 mediante el backend global `STORAGES` configurado por `core.storage_config` |

Servicios externos: Redis (caché e índice de búsqueda), Celery (notificaciones de sync móvil vía
`apps.keyboard_api.tasks`), ffmpeg y HTTP saliente para metadatos Open Graph / YouTube oEmbed y
favicons de Google. **Sin integración directa con Sentry** — los errores afloran por el manejador
global.

`apps/boards/signals.py` se registra desde `apps.py` y dispara las tareas de keyboard-sync más la
contabilidad de `BoardDeleteLog`.

La configuración a nivel de contenedor (disponibilidad de ffmpeg, servicio Redis, workers Celery)
está documentada en [`docs/docker.es.md`](../../docs/docker.es.md).
