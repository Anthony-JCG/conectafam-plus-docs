# streaming

## Descripción

Gestión de sesiones en vivo. El usuario configura un stream con página de espera, página pública de
visualización y una página post-finalización para convertir asistentes en contactos. El vídeo se
sirve como HLS, transcodificado en segundo plano en lugar de emitirse en tiempo real.

Relación con las apps núcleo:

- **`user_levels`** — límites de creación y visibilidad (`check_action_allowed`,
  `get_model_visible_queryset`, `collect_downgrade_blocks`). Esta app implementa la regla del
  **derivado PRO**: un usuario PRO puede crear un stream derivado (`parent_stream`) a partir de un
  original de la línea ascendente mediante `use_shared_stream`; el derivado es personal mientras el
  original sigue siendo la fuente compartida de la línea.
- **`core`** — procesamiento de archivos, la tarea Celery de transcodificación HLS, wrappers de
  Redis y constantes (`MAX_SIMULTANEOUS_STREAMS`, `MAX_VIEWERS_PER_STREAM`).
- **`users.User`** — propietario de cada stream.
- **`communication`** — los espectadores registrados pasan a filas `Contact`, y la página
  post-finalización enlaza a un `WhatsAppLink`.

## Modelos y datos

| Modelo | Relaciones |
|---|---|
| `Streaming` | FK → `users.User`; FK → `self` (`parent_stream`, derivados PRO). Contiene `video_file`, `hls_manifest`, `is_processing`, datos de programación |
| `PostFinalizationPage` | OneToOne → `Streaming`; FK → `communication.WhatsAppLink` (`link_whatsapp`) |
| `SliderImage` | FK → `PostFinalizationPage` |

Manejo de vídeo: al guardar un `Streaming` con un `video_file` nuevo se encola
`core.tasks.process_video_task`, que ejecuta ffmpeg para generar el manifiesto HLS y actualiza
`is_processing`. Una señal `post_delete` elimina el árbol HLS generado de `default_storage`.

El conteo de espectadores usa dos capas: un contador Redis para el número mostrado, y un set en la
caché de Django indexado por sesión/IP para la lista real de asistentes.

No hay `services.py` ni `utils.py`; la lógica vive en `views.py`, `forms.py` y `tasks.py`
(emails de recordatorio programados, encolados desde `views._schedule_stream_emails`).

## Vistas e integración frontend

**Esta app no usa HTMX.** Los formularios hacen post normal y los contadores en vivo consultan
endpoints JSON desde `static/js/stream-page.js` y `streaming_modal.js`.

Prefijo de URL: **`/streaming/`**

| URL | Vista | Respuesta |
|---|---|---|
| `waiting-page/` | `waiting_page` | Panel de gestión del stream (HTML) |
| `stream-page/<user_id>_<stream_id>/` | `stream_page` | Página pública del stream, o la post-finalización una vez terminado (HTML) |
| `preview/stream/<id>/` · `preview/post-page/<id>/` | `stream_page_preview`, `post_page_preview` | Previsualizaciones solo del propietario (HTML) |
| `save-waiting-page/` | `save_waiting_page` | Crea/actualiza el stream (redirect) |
| `save-post-finalization-page/` | `save_post_finalization_page` | CRUD de la página post-finalización (redirect) |
| `delete-streaming/` | `delete_streaming` | Elimina el stream (redirect) |
| `register-stream-viewer/` | `register_stream_viewer` | Registra un espectador como contacto (JSON) |
| `join-stream/` · `leave-stream/` · `get-stream-viewers/` | `join_stream`, `leave_stream`, `get_stream_viewers` | Contadores de espectadores en vivo (JSON) |
| `copy/<id>/` | `copy_stream` | Copia un stream visible (redirect) |
| `use-shared-stream/` | `use_shared_stream` | Crea el derivado PRO a partir de un original de la línea ascendente (redirect) |

## Configuración y dependencias

| Setting | Propósito |
|---|---|
| `FFMPEG`, `FFPROBE` | Transcodificación HLS, ejecutada por `core.tasks.process_video_task` |
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Contadores de espectadores |
| `R2_*` / `STORAGES` | Vídeos fuente y segmentos HLS generados viven en el backend de media (Cloudflare R2 en producción) |
| `MAX_SIMULTANEOUS_STREAMS`, `MAX_VIEWERS_PER_STREAM` (desde `core.const`) | Topes a nivel de aplicación |
| Settings de email (SMTP) | Emails de recordatorio programados enviados desde `tasks.py` |

Servicios externos: Redis, Celery (emails de recordatorio y transcodificación de vídeo), ffmpeg.
**Sin integración con Sentry ni Stripe** en esta app.

Servir HLS desde Cloudflare R2 depende de la configuración global de media descrita en
[`apps/core/README.es.md`](../core/README.es.md); la disponibilidad de ffmpeg a nivel de contenedor y
la configuración del worker Celery están documentadas en [`docs/docker.es.md`](../../docs/docker.es.md).

Dependencias de la app: `communication`, `core`, `main` (`notifications_texts`), `user_levels`, `users`.
