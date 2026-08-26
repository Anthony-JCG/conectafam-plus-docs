# core

## Descripción

Infraestructura transversal del monolito. `core` no posee dominio de negocio: aporta los
bloques técnicos que consumen el resto de apps — procesamiento de medios, acceso a Redis,
notificaciones push, helpers de respuesta HTMX, formularios y widgets base, constantes globales
y el context processor de plantillas.

La dirección de dependencias es deliberada: las apps de negocio importan desde `core`, y `core`
solo vuelve a ellas mediante **importaciones diferidas dentro de funciones** (`views.py`,
`utils/notifications.py`, `utils/social_preview.py`) para resolver objetos en tiempo de ejecución
sin ciclos de importación.

Relación con las apps centrales:

- **`users.User`** — no se almacena aquí, pero los servicios de notificación lo reciben como
  argumento.
- **`user_levels`** — `core` nunca decide permisos. `OBJECT_TYPE_CHOICES` (definido aquí) alimenta
  `SharedObjectRecord` / `DowngradedObjectFlag` y el receptor de limpieza `post_delete`.

## Modelos y datos

**Esta app no define modelos.** `apps/core/migrations/` existe solo para que la app sea instalable.

El estado que gestiona `core` vive en Redis, no en la base de datos:

| Clave | Escrita por | Contenido |
|---|---|---|
| `notifications:<user_id>` | `utils/notifications.py` | Feed de notificaciones por usuario (lista acotada, TTL) |
| `subscriptions:<user_id>` | `utils/notifications.py` | Suscripciones Web Push / FCM registradas |
| `<flag_name>` (flags de procesamiento) | `utils/redis_bd.py` | Tokens de exclusión mutua con TTL para trabajos de imagen/vídeo |

Las constantes de dominio compartidas entre apps viven en `const.py`:

- `LABEL_*` — cadenas `app_label.ModelName` de cada modelo compartible (`LABEL_CHALLENGE_MODEL`,
  `LABEL_INCENTIVE_MODEL`, `LABEL_STREAMING_MODEL`, `LABEL_SCHEDULED_TASK`…).
- `OBJECT_TYPE_CHOICES` — choices derivados de esas etiquetas; los consumen los modelos de
  `user_levels` y la limpieza `post_delete` en `user_levels/signals.py`.
- Límites duros (`LIMIT_USER_LINKS`, `MAX_SIMULTANEOUS_STREAMS`, `MAX_VIEWERS_PER_STREAM`,
  `MAX_CHALLENGES_PER_USER`) y valores de marca (`WEBSITE_NAME`, `COMPANY_NAME`).
- Identidades de arranque (`USER_ROOT`, `FIRST_LEADER_PRO`) cuyo valor cambia según
  `settings.DEBUG`.

### Utilidades (`utils/`)

| Módulo | Contenido principal |
|---|---|
| `__init__.py` | `get_embed_resource_url` (YouTube nocookie), `get_share_preview_url`, `get_country_choices` |
| `files.py` | `process_image_to_webp`, `process_video_to_hls` y los hooks `process_*_field_if_changed` llamados desde `Model.save()`; nombres de archivo por hash de contenido y borrado del árbol de almacenamiento |
| `redis_bd.py` | `redis_get/set/delete_key/delete_pattern`, `acquire_processing_flag`, `release_processing_flag`, `processing_flag_exists` |
| `notifications.py` | `push_notification`, `notify_downline`, `send_personal_notification`, registro de suscripciones |
| `web_fcm.py` | `send_web_push_to_token`, `is_web_fcm_ready` — entrega por Firebase Cloud Messaging |
| `fcm_errors.py` | Clasifica fallos FCM en token obsoleto vs transitorio; backoff `fcm_retry_countdown` |
| `fcm_observability.py` | `report_fcm_event` — reenvía anomalías FCM a Sentry |
| `htmx.py` | `attach_toast_trigger(response, message)` y `htmx_error_response(msg, status=422)` — el contrato de respuesta HTMX usado en todo el proyecto |
| `pdf_preview.py` | `pdf_first_page_to_webp_bytes`, `store_pdf_preview_bytes`, `clear_pdf_preview` (PyMuPDF) |
| `social_preview.py` | `resolve_share_preview_object`, `build_share_preview_data` — metadatos Open Graph |
| `task_days.py` | `parse_task_days`, `get_tasks_for_day` — filtrado de días de tareas recurrentes |

### Tareas Celery (`tasks.py`)

| Tarea | Descripción |
|---|---|
| `process_image_task` | Convierte un campo de imagen a WebP para cualquier `app_label.Model`. Flag Redis, TTL 10 min. |
| `process_video_task` | Genera el manifiesto HLS vía ffmpeg. Flag Redis, TTL 1 h. |

## Vistas e integración frontend

**Esta app no usa HTMX.** Su propia plantilla (`templates/index.html`, la landing de marketing
pública) no contiene atributos `hx-*`; sus endpoints AJAX responden con `JsonResponse`.

`core` es, no obstante, el **proveedor** del contrato HTMX de todo el proyecto: `utils/htmx.py`
aporta el helper de toast `HX-Trigger` y la respuesta de error 422 que consumen `boards`,
`communication`, `landing` y `main`, y que el cliente lee en el ciclo de vida genérico de
formularios modales en `static/js/core.js`.

| Vista | URL | Respuesta |
|---|---|---|
| `index` | `/` | Redirección a `home` |
| `init_page` | `/home/` | Landing de marketing pública (HTML) |
| `sw_js` | root | Script del service worker |
| `set_timezone` | root | JSON — guarda la zona horaria del navegador en sesión |
| `update_drag_drop` | root | JSON — reordenación genérica por drag-and-drop |
| `redirect_to_whatsapp_link` | root | Redirección al enlace de WhatsApp de un usuario |
| `share_preview` | root | Intersticial HTML con metadatos Open Graph antes de redirigir |

Componentes frontend compartidos ofrecidos a otras apps: `BaseForm` (`forms.py`), widgets
personalizados (`widgets.py`), `templatetags/core_tags.py` (`tojson`, `social_share_meta`,
`share_preview_url`) y `context_processor.templates_vars`, que inyecta flags de nivel y constantes
globales en cada plantilla.

## Configuración y dependencias

Ajustes consumidos por esta app (`Platform/settings.py`):

| Setting | Usado por | Notas |
|---|---|---|
| `REDIS_URL`, `REDIS_KEY_PREFIX`, `USER_LEVEL_CACHE_TTL` | `utils/redis_bd.py` | Prefijo y TTL por defecto de cada clave escrita aquí |
| `FFMPEG`, `FFPROBE` | `utils/files.py` | Rutas de binarios para transcodificación HLS; presentes en la imagen Docker |
| `FIREBASE_CREDENTIALS_JSON`, `FIREBASE_WEB_*`, `FIREBASE_WEB_VAPID_KEY` | `utils/web_fcm.py` | Credenciales Web Push |
| `SENTRY_DSN` | `utils/fcm_observability.py` | Las anomalías FCM se reportan con `sentry_sdk` |
| `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_CUSTOM_DOMAIN` | `storage_config.py` | Backend de media Cloudflare R2 |
| `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE` | Pipeline de subida | Límites aplicados antes del procesamiento en segundo plano |

**Cloudflare R2** se cablea aquí: `storage_config.py` expone `r2_media_storage_enabled()` y
`build_r2_default_storage()`, y `settings.py` solo activa el backend S3 cuando el entorno es
producción, `TEST_ENVIRONMENT` está desactivado y están presentes todas las credenciales R2. La
media se sirve entonces desde `https://{R2_CUSTOM_DOMAIN}/media/` con `querystring_auth=False`. Los
archivos estáticos **no** van a R2 — usan `ManifestStaticFilesStorage` y los sirve Nginx.

Dependencias externas: Redis, Celery, ffmpeg, Pillow, PyMuPDF, `firebase-admin` / `pywebpush`,
`django-storages` + `boto3`. La configuración a nivel de contenedor de todo esto está documentada en
[`docs/docker.es.md`](../../docs/docker.es.md).

Comandos de gestión: `clean_old_notifications`, `clear_push_subscriptions`.
