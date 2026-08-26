# landing

## Descripción

Constructor de landing pages basado en bloques. Los usuarios componen páginas públicas de captación
a partir de bloques ordenados (hero, texto, vídeo, PDF, carrusel, FAQ, lista de aprendizaje, CTA,
formulario de contacto) y las publican con una URL larga o con un slug «bonito» corto. Los líderes
pueden compartir una landing como **plantilla** que los usuarios de su línea descendente bifurcan
en su propia copia.

El mismo motor sostiene `boards`: un elemento de tablero tipo `page` crea un `LandingPage` con
`page_context=board`, renderizado a través de `services/board_editor.py`.

Relación con las apps núcleo:

- **`user_levels`** — los límites de creación y el gating PRO entran por
  `services/landing_permissions.py` (`check_landing_create_allowed`,
  `assert_blank_landing_create_allowed`); las constantes `RESTRICTED_ALERT_*` impulsan los modales
  de upgrade.
- **`core`** — `BaseForm`, procesamiento de archivos, normalización de payloads Quill, miniaturas
  PDF y el contrato HTMX `attach_toast_trigger` / `htmx_error_response`.
- **`users.User`** — propietario de `LandingPage` y `LandingPageUserTemplateState`.
- **`communication`** — los bloques y CTAs de landing apuntan a `WhatsAppLink`; los formularios de
  contacto enviados crean filas `Contact`.
- **`boards`** — los bloques pueden importarse desde `BoardItem`, y una página de tablero es una
  landing.

## Modelos y datos

| Modelo | Relaciones |
|---|---|
| `LandingPage` | FK → `users.User`; FK → `self` (`source_landing`, la plantilla de la que se bifurcó) |
| `LandingPageBlock` | FK → `LandingPage`; FK opcional → `boards.BoardItem`; FK → `communication.WhatsAppLink` |
| `LandingPageLearningItem` | FK → `LandingPageBlock` |
| `LandingPageFaqItem` | FK → `LandingPageBlock` |
| `LandingPageCarouselItemBlock` | FK → `LandingPageBlock` |
| `LandingPageCustomization` | OneToOne → `LandingPage` — tema, colores, tipografía |
| `LandingPageUserTemplateState` | FK → `users.User`; FK → `LandingPage` (`template`); OneToOne → `LandingPage` para `share_landing` y `fork_landing`; FK → `communication.WhatsAppLink` (`default_whatsapp_link`) |
| `LandingPageBuilder` | OneToOne → `LandingPage`. Payload GrapesJS; **aún no hay vistas que lo expongan** |

El contenido de la página es enteramente dirigido por bloques: no hay flags booleanos por sección en
`LandingPage`. El orden, la visibilidad y el tipo de bloque viven en `LandingPageBlock`.

Los bloques PDF almacenan un `document_thumbnail` generado en el servidor por
`services/document_preview.py` (reutilizando `core.utils.pdf_preview`), de modo que la página
pública renderiza una imagen en lugar de arrancar PDF.js.

### Servicios

| Módulo | Responsabilidad |
|---|---|
| `services/landing_permissions.py` | Permisos de creación, share/fork, copia profunda, querysets de listado |
| `services/landing_blocks.py` | Persistencia de bloques e ítems anidados |
| `services/landing_serialize.py` | Serialización JSON y filas de tabla |
| `services/landing_preview.py` | Renderizado de preview dentro de un savepoint + rollback |
| `services/landing_slugs.py` | Generación de `public_slug` para URLs bonitas |
| `services/document_preview.py` | Sincronización de miniaturas WebP para bloques PDF |
| `services/board_editor.py` | Integración de páginas de tablero e importación de `BoardItem` |
| `utils.py` | Resúmenes de bloques, desbloqueo de sesión, helpers AJAX/WhatsApp, fusión de formularios |

## Vistas e integración frontend

**Esta app usa HTMX** para el dashboard de landings y para la manipulación de bloques dentro del
editor de contenido.

Prefijo de URL: **`/landing-page/`**. Las URLs bonitas se montan por separado en
`Platform/urls.py` como `p/<slug>/` → `landing_pretty`.

### Endpoints HTMX

| Endpoint | Name | Comportamiento HTMX |
|---|---|---|
| `load-basic-form/` | `load_landing_basic_form` | GET parcial con el formulario de datos básicos; solicitado vía `htmx.ajax` desde `landing-page.html` |
| `save/` | `save_landing_page` | La rama HTMX devuelve un parcial + toast `HX-Trigger`; las llamadas no HTMX siguen recibiendo JSON |
| `delete/` | `delete_landing_page` | Parcial + toast `HX-Trigger` |
| `toggle-pretty-url/` | `toggle_landing_pretty_url` | Vuelve a renderizar la tabla de landings |
| `edit/<id>/add-block/` | `add_landing_block` | Añade un fragmento de fila de bloque |
| `edit/<id>/add-nested-item/` | `add_landing_nested_item` | Añade una fila de ítem anidado (carrusel, FAQ, aprendizaje) |
| `edit/<id>/import-board-items/` | `import_board_items_to_landing` | Inyecta bloques construidos a partir de `BoardItem`s seleccionados |
| `block/delete/` | `delete_landing_block` | Elimina un bloque, toast `HX-Trigger` |

Los errores de validación devuelven `htmx_error_response` (422). Plantillas de envío:
`components/modal-landing-basic.html` y `components/modal-delete-landing.html` (ambas con
`data-close-modal`) y `components/table-landings.html`. Dentro del editor, las peticiones se emiten
de forma programática con `htmx.ajax` desde `static/js/landing_blocks.js` y
`static/js/landing_board_picker.js`.

### Endpoints HTML y JSON

| Ruta | Name | Respuesta |
|---|---|---|
| `<username>/<type_contact>_<landing_id>/` | `landing_template` | Landing pública; el POST captura un contacto |
| `p/<slug>/` (montada en la raíz) | `landing_pretty` | Misma vista detrás del slug corto |
| `""` | `landing_page` | Dashboard autenticado con el listado de landings del usuario |
| `edit/<id>/` | `edit_landing_content` | Editor de bloques |
| `edit/<id>/preview/` | `preview_landing_content` | POST → preview HTML renderizado (savepoint + rollback) |
| `share-template/` | `share_leader_landing` | JSON — publica una plantilla de líder |
| `duplicate-template/` | `duplicate_landing_template` | JSON — bifurca una plantilla en la cuenta del usuario |

Módulos frontend en `static/js/`: `landing_blocks.js` (gestor de bloques e ítems anidados),
`landing_ajax.js` (pipeline de guardado y sync de preview del carrusel),
`landing_content_editor.js` (orquestación del editor; refresca desde la base de datos tras cada
guardado), `landing_board_picker.js`, `landing_pdf_block.js` (fallback lazy de PDF.js vía
`IntersectionObserver`, solo cuando no existe miniatura server-side). Estilos públicos en
`static/css/landing-page.css`.

## Configuración y dependencias

| Setting | Propósito |
|---|---|
| `R2_*` / `STORAGES` | Imágenes, vídeos y PDFs de bloques se almacenan mediante el backend global de media (Cloudflare R2 en producción) |
| `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE` | Subidas de archivos de bloques |
| Ajustes de email (SMTP) | Notificaciones de captura de contacto enviadas a través de `apps.users.utils.send_email` |

Integraciones externas: YouTube (embeds nocookie y miniaturas `i.ytimg.com`), deep links de
WhatsApp y un **Facebook Pixel** opcional por landing (`facebook_pixel_id`).

Esta app **no usa Sentry, Redis ni Celery de forma directa**; el almacenamiento de media se hereda
de la configuración global descrita en [`apps/core/README.es.md`](../core/README.es.md) y
[`docs/docker.es.md`](../../docs/docker.es.md).

Dependencias de la app: `core`, `users`, `user_levels`, `communication`, `boards`, `links`.
