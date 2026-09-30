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
| `Board` | Contenedor del usuario: título, imagen de portada, orden, `share_token`, `allow_duplicate_on_share`, `is_public`, `is_client_area`. FK → `users.User` |
| `BoardFolder` | Carpetas anidables (`parent` FK → self), ordenables en el mosaico. FK opcional `catalog_folder` → `BoardFolder` para las carpetas sombra del área de clientes |
| `BoardItem` | Elemento del mosaico. Tipos: `text`, `image`, `link`, `video`, `voice`, `pdf`, `youtube`, `page`. Archivos hasta 10 MB. FK opcional → `landing.LandingPage` |
| `BoardCollaborator` | Usuario invitado. Los colaboradores PRO+ tienen acceso de lectura y edición; los colaboradores Basic son de solo lectura. Único en `(board, user)` |
| `BoardLibraryEntry` | Referencia a un tablero compartido guardado en la biblioteca propia (solo lectura) |
| `BoardDeleteLog` | Registro append-only de tableros eliminados de forma permanente. `board_id` / `user_id` son enteros simples porque la fila `Board` ya no existe. Lo consume **solo** el endpoint de delta-sync de la keyboard API para que los clientes móviles sepan qué purgar |

### Boards del área de clientes

Hay dos boards con `is_client_area=True`, pero el asesor solo ve **uno**, "Área de clientes":

| Board | Dueño | Tipos permitidos | Quién lo crea |
|---|---|---|---|
| Catálogo de sistema (`CLIENT_AREA_CATALOG_TITLE`, carpetas Nutrición / Deporte / Videoteca / Otros) | FAM TEAM / `USER_ROOT` | PDF, imagen (`CLIENT_AREA_CATALOG_ITEM_TYPES`); Videoteca admite además vídeo subido y YouTube (`CLIENT_AREA_CATALOG_FOLDER_EXTRA_ITEM_TYPES`) | Migraciones `0009` / `0010`; `manage.py seed_client_area_board` (idempotente) |
| Board propio del área de clientes ("Área de clientes", `CLIENT_AREA_OWN_BOARD_TITLE`) | Cada asesor con derecho, privado | Carpetas, texto, imagen, PDF, vídeo subido, YouTube (`CLIENT_AREA_OWN_ITEM_TYPES`) | `client_area_catalog.ensure_user_client_area_board` la primera vez que hace falta (home de boards, panel del área de clientes) |

Solo `USER_ROOT` edita el catálogo, y `USER_ROOT` no ve nada más. El asesor gestiona su board con
las vistas de boards de siempre.

#### Vista unificada

El board propio es la única puerta de entrada del asesor (home de boards, búsqueda y selector del
área de clientes). `client_area_catalog.get_merged_catalog_board(user, board)` devuelve el catálogo
cuando `board` es el board propio del usuario, y la vista junta los dos:

| Dónde | Fichas |
|---|---|
| Raíz del board | Solo las carpetas del catálogo (solo lectura) |
| Carpeta del catálogo | Las de root (solo lectura) y después las de la carpeta sombra del asesor |
| Carpeta propia | Las propias |

- `utils.build_view_mosaic_tiles` marca las fichas del catálogo con `read_only: true` *después* de
  leer la caché. Cada board conserva su propia entrada Redis del mosaico (board/carpeta), así que en
  caché nunca hay datos de un usuario concreto.
- `utils.find_view_folder` / `utils.get_view_item` resuelven carpetas y elementos del catálogo bajo
  la URL del board propio (`board_folder`, `board_mosaic_data`, `board_item_tile`). Los archivos los
  sigue sirviendo `board_item_file` sobre el catálogo (la ficha ya lleva esa URL).
- `board_detail` sobre el catálogo redirige al asesor a su board (misma carpeta y misma query, p. ej.
  `open_item` desde la búsqueda). El índice de búsqueda incluye carpetas y elementos del catálogo
  como fichas de solo lectura, pero no una entrada del board catálogo.
- `mosaic.js` no deja arrastrar ni seleccionar fichas de solo lectura (el selector del área de
  clientes sí las elige) y no las manda al reordenar; `item-viewer.js` les oculta editar, mover y
  borrar.

#### Raíz bloqueada

En la raíz de un board del área de clientes no se añade nada, ni root ni los asesores: ahí solo
están las carpetas del catálogo (Nutrición / Deporte / Videoteca / Otros), y el contenido va dentro
de ellas (o de sus subcarpetas).

- UI: `utils.build_board_detail_context` calcula `can_add`, así que `board-detail.html` no muestra
  "Añadir" en la raíz; `folder_options` no ofrece "Raíz del board" en estos boards.
- Servidor: con `client_area_root_locked(board, folder)`, `save_board_folder` (alta),
  `save_board_item` (alta), `move_board_item` y el movimiento múltiple responden
  `CLIENT_AREA_ROOT_LOCKED_MESSAGE` si el destino es la raíz. Al editar se mantiene la carpeta del
  elemento.
- Los tipos permitidos dependen de la carpeta: `client_area_root_folder(folder)` sube hasta la
  carpeta raíz (una carpeta sombra cuenta como su carpeta del catálogo) y
  `client_area_item_types(board, folder)` suma sus `CLIENT_AREA_CATALOG_FOLDER_EXTRA_ITEM_TYPES`.
  `item-modal.js` manda `folder_id` a `load_board_item_form` para que el menú de tipos cuadre con
  la carpeta.

Las carpetas propias de primer nivel creadas antes de esta regla ya no son válidas; la migración
`0012` mueve a Otros lo que hubiera suelto en la raíz.

#### Carpetas sombra

El asesor puede añadir elementos y subcarpetas dentro de las carpetas de root; la carpeta del
catálogo sigue siendo de solo lectura (ni renombrar ni borrar: `is_catalog_folder` oculta esas
acciones).

- Lo que añade se guarda en una *carpeta sombra* de su board: `BoardFolder.catalog_folder` (FK
  opcional, una por board y carpeta del catálogo) apunta a la carpeta del catálogo.
- `client_area_catalog.ensure_shadow_folder` la crea con la primera escritura, a través de
  `utils.find_write_folder` / `get_write_folder` (los usan `save_board_item`, `save_board_folder`,
  `move_board_item` y el movimiento múltiple): un id de carpeta del catálogo que llega al board
  propio se traduce a su sombra.
- Las carpetas sombra están en la raíz del board propio, que la vista combinada nunca lista (solo
  muestra las carpetas del catálogo). Si se abre una por su id se ve su carpeta del catálogo, en las
  opciones de mover aparece con el título del catálogo, y el índice de búsqueda incluye sus
  elementos (URL `board_folder(propio, sombra)`) sin una entrada de carpeta aparte.
- Si root borra la carpeta del catálogo, `SET_NULL` deja la sombra como carpeta normal y no se
  pierde nada.

Las escrituras siguen atadas al board de la URL: guardar, borrar, mover, reordenar y las acciones
múltiples buscan con `board=board`, de modo que un id de elemento del catálogo enviado por el board
propio da 404 o se ignora. Nada se mueve de un board a otro.

¿Por qué dos boards detrás de una sola vista y no un dueño por elemento? Todo en boards va por board
(caché del mosaico, índice de búsqueda, `board_item_file`, operaciones múltiples, reordenado). Con un
board privado se aprovecha todo el CRUD con un solo FK opcional y sin comprobar el dueño elemento a
elemento; la mezcla solo ocurre al leer.

#### Permisos

Todo está en `services/board_permissions.py`; el derecho sale de `user_levels`
(`check_action_allowed(CLIENT_AREA_MODEL_KEY, ACCESS_ACTION_KEY)`) o del add-on `client_area`.

| Función | Regla |
|---|---|
| `user_can_view_client_area_board` | El board propio, o el catálogo mientras haya derecho; nunca el de otro asesor. Biblioteca, colaboradores y enlaces compartidos no cuentan (`board_share`, `save_shared_board` y `resolve_board_read_access` ignoran estos boards) |
| `user_can_manage_board_collaborators` | Siempre `False` en boards del área de clientes |
| `user_can_edit_board` | Solo el dueño: `USER_ROOT` en el catálogo y el asesor con derecho en el suyo |
| `user_may_write_board_content` | No exige las rutas de escritura del plan en estos boards; `RouteLevelAccessMiddleware` (`CLIENT_AREA_BOARD_WRITE_ROUTES`) deja a un Basic con el add-on usarlas únicamente en su propio board |
| `get_client_area_catalog_boards_queryset(user)` | Primero el catálogo y después el board propio. Lo usan el índice de búsqueda y, en el área de clientes, la búsqueda del selector y los formularios |
| `client_area_item_types(board, folder)` / `board_allows_item_type` / `require_client_area_item_type` | Tipos permitidos por board y carpeta raíz (Videoteca suma vídeo y YouTube); también alimentan el menú "Añadir" (`client_area_add_menu(board, folder)`) y `load_board_item_form` |
| `client_area_root_locked(board, folder)` | `True` en la raíz de un board del área de clientes: ahí no se crea ni se mueve ninguna carpeta o elemento |

En la configuración solo se editan título, descripción y portada, y estos boards no se pueden
borrar desde la interfaz (`delete_board` / `save_board` los descartan). El flag además los deja
fuera de la sincronización del teclado (`_get_accessible_board_ids`) y de los límites de creación y
el exceso de objetos de `BOARDS_MODEL_KEY`.

#### Migraciones

| Migración | Cambio |
|---|---|
| `0009_seed_client_area_catalog_board` | Crea el board catálogo y sus carpetas para `USER_ROOT` si no existen |
| `0010_set_client_area_catalog_cover` | Pone la portada por defecto (`static/img/min_board.jpg`, tal cual, sin WebP) si el catálogo no tiene |
| `0011_boardfolder_catalog_folder` | Añade `BoardFolder.catalog_folder` (carpetas sombra) |
| `0012_client_area_root_folders_only` | Datos: crea las carpetas raíz del catálogo que falten (Nutrición / Deporte / Videoteca / Otros) y mueve a Otros las carpetas y elementos sueltos en la raíz de un board del área de clientes (a la carpeta del catálogo o a la carpeta sombra del asesor) |

`0009`, `0010` y `0012` solo usan modelos históricos (`apps.get_model`), así que `0011` y los cambios de
esquema posteriores se aplican sin problema detrás de ellas en una base de datos nueva. Las dos se
saltan con un aviso si todavía no existe `USER_ROOT` (o el board catálogo); `seed_client_area_board`
lo crea después. `0010` falla si no encuentra la portada estática.

### Lógica de acceso

| Tipo de usuario | Ver | Editar | Gestionar | Duplicar |
|---|---|---|---|---|
| Propietario | ✓ | ✓ | ✓ | ✓ |
| Colaborador (PRO+) | ✓ | ✓ | — | ✓ |
| Colaborador (Basic) | ✓ | — | — | ✓ |
| Entrada de biblioteca | ✓ | — | — | Solo si `allow_duplicate_on_share` |
| Tablero público | ✓ | — | — | — |

### Permisos según el plan

| Nivel | Acceso | Límite de creación | Compartir con el equipo (`is_public`) |
|---|---|---|---|
| Basic | Leer públicos/compartidos; solo lectura como colaborador | — | — |
| Pro | Sí | 1 | — |
| Leader | Sí | 3 | Sí, dentro de su burbuja de visibilidad |
| Leader Pro | Sí | Ilimitado | Sí, mismas reglas de burbuja |

Las rutas restringidas devuelven 404 a través de `RouteLevelAccessMiddleware`. Los colaboradores de
nivel Basic conservan acceso de lectura en los tableros en los que colaboran, sin permiso de
escritura. Gestionar colaboradores (añadir/quitar) es una acción de propietario Leader / Leader Pro;
los propietarios PRO ven la sección detrás del overlay de acceso restringido.

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
| `services/board_cover.py` | Reprocesa la portada del tablero a WebP; asigna portadas por defecto desde static |
| `services/item_titles.py` | Resuelve títulos de elementos desde fuentes externas (YouTube, metadatos de enlace) |
| `services/voice_convert.py` | WebM → MP3 mediante ffmpeg; lanza `VoiceConversionError` |
| `services/folder_options.py` | Opciones de carpeta para el desplegable legacy del modal de mover; el selector de destino carga carpetas bajo demanda desde el endpoint JSON del mosaico |
| `services/client_area_catalog.py` | Boards del área de clientes: asegurar el catálogo y el board propio, resolver el catálogo combinado, carpetas sombra |
| `services/client_area_uploads.py` | Lo que se sube desde el panel del área de clientes se convierte en un elemento del board: `get_client_area_upload_folder(user, root_title, subfolder_title)` (la carpeta del catálogo para `USER_ROOT`, la carpeta sombra para un asesor; la subcarpeta se crea al primer uso) y `create_client_area_item(folder, uploaded_file=, youtube_url=)` |
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
