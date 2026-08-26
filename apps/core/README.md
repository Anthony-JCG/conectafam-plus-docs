# core

## Description

Cross-cutting infrastructure for the monolith. `core` owns no business domain: it provides the
technical building blocks every other app consumes — media processing, Redis access, push
notifications, HTMX response helpers, base forms and widgets, global constants, and the template
context processor.

Dependency direction is deliberate: business apps import from `core`, and `core` only reaches back
into them through **lazy imports inside functions** (`views.py`, `utils/notifications.py`,
`utils/social_preview.py`) to resolve objects at runtime without creating import cycles.

Relationship to the central apps:

- **`users.User`** — not stored here, but received as an argument by the notification services.
- **`user_levels`** — `core` never decides permissions. `OBJECT_TYPE_CHOICES` (defined here) feeds
  `SharedObjectRecord` / `DowngradedObjectFlag` and the `post_delete` cleanup receiver.

## Models and Data

**This app defines no models.** `apps/core/migrations/` exists only to keep the app installable.

State that `core` manages lives in Redis rather than in the database:

| Key | Written by | Contents |
|---|---|---|
| `notifications:<user_id>` | `utils/notifications.py` | Per-user notification feed (capped list, TTL) |
| `subscriptions:<user_id>` | `utils/notifications.py` | Registered Web Push / FCM subscriptions |
| `<flag_name>` (processing flags) | `utils/redis_bd.py` | Mutual-exclusion tokens with TTL for image/video jobs |

Domain constants shared across apps live in `const.py`:

- `LABEL_*` — `app_label.ModelName` strings for every shareable model (`LABEL_CHALLENGE_MODEL`,
  `LABEL_INCENTIVE_MODEL`, `LABEL_STREAMING_MODEL`, `LABEL_SCHEDULED_TASK`…).
- `OBJECT_TYPE_CHOICES` — choices derived from those labels; consumed by `user_levels` models and by
  the `post_delete` cleanup in `user_levels/signals.py`.
- Hard limits (`LIMIT_USER_LINKS`, `MAX_SIMULTANEOUS_STREAMS`, `MAX_VIEWERS_PER_STREAM`,
  `MAX_CHALLENGES_PER_USER`) and branding values (`WEBSITE_NAME`, `COMPANY_NAME`).
- Bootstrap identities (`USER_ROOT`, `FIRST_LEADER_PRO`) that switch value depending on
  `settings.DEBUG`.

### Utilities (`utils/`)

| Module | Key contents |
|---|---|
| `__init__.py` | `get_embed_resource_url` (YouTube nocookie), `get_share_preview_url`, `get_country_choices` |
| `files.py` | `process_image_to_webp`, `process_video_to_hls`, and the `process_*_field_if_changed` hooks called from `Model.save()`; content-hash file naming and storage-tree deletion |
| `redis_bd.py` | `redis_get/set/delete_key/delete_pattern`, `acquire_processing_flag`, `release_processing_flag`, `processing_flag_exists` |
| `notifications.py` | `push_notification`, `notify_downline`, `send_personal_notification`, subscription registry |
| `web_fcm.py` | `send_web_push_to_token`, `is_web_fcm_ready` — Firebase Cloud Messaging delivery |
| `fcm_errors.py` | Classifies FCM failures into stale-token vs transient; `fcm_retry_countdown` backoff |
| `fcm_observability.py` | `report_fcm_event` — forwards FCM anomalies to Sentry |
| `htmx.py` | `attach_toast_trigger(response, message)` and `htmx_error_response(msg, status=422)` — the HTMX response contract used across the project |
| `pdf_preview.py` | `pdf_first_page_to_webp_bytes`, `store_pdf_preview_bytes`, `clear_pdf_preview` (PyMuPDF) |
| `social_preview.py` | `resolve_share_preview_object`, `build_share_preview_data` — Open Graph metadata |
| `task_days.py` | `parse_task_days`, `get_tasks_for_day` — recurring-task day filtering |

### Celery tasks (`tasks.py`)

| Task | Description |
|---|---|
| `process_image_task` | Converts an image field to WebP for any `app_label.Model`. Redis flag, TTL 10 min. |
| `process_video_task` | Generates the HLS manifest via ffmpeg. Redis flag, TTL 1 h. |

## Views and Frontend Integration

**This app does not use HTMX.** Its own template (`templates/index.html`, the public marketing
landing) contains no `hx-*` attributes; its AJAX endpoints answer with `JsonResponse`.

`core` is, however, the **provider** of the project-wide HTMX contract: `utils/htmx.py` supplies the
`HX-Trigger` toast helper and the 422 error response consumed by `boards`, `communication`,
`landing`, and `main`, and read on the client by the generic modal-form lifecycle in
`static/js/core.js`.

| View | URL | Response |
|---|---|---|
| `index` | `/` | Redirect to `home` |
| `init_page` | `/home/` | Public marketing landing (HTML) |
| `sw_js` | root | Service worker script |
| `set_timezone` | root | JSON — stores the browser timezone in session |
| `update_drag_drop` | root | JSON — generic drag-and-drop reordering |
| `redirect_to_whatsapp_link` | root | Redirect to a user's WhatsApp link |
| `share_preview` | root | HTML interstitial carrying Open Graph metadata before redirecting |

Shared frontend components provided to other apps: `BaseForm` (`forms.py`), custom widgets
(`widgets.py`), `templatetags/core_tags.py` (`tojson`, `social_share_meta`, `share_preview_url`), and
`context_processor.templates_vars`, which injects level flags and global constants into every
template.

## Configuration and Dependencies

Settings consumed by this app (`Platform/settings.py`):

| Setting | Used by | Notes |
|---|---|---|
| `REDIS_URL`, `REDIS_KEY_PREFIX`, `USER_LEVEL_CACHE_TTL` | `utils/redis_bd.py` | Prefix and default TTL for every key written here |
| `FFMPEG`, `FFPROBE` | `utils/files.py` | Binary paths for HLS transcoding; present in the Docker image |
| `FIREBASE_CREDENTIALS_JSON`, `FIREBASE_WEB_*`, `FIREBASE_WEB_VAPID_KEY` | `utils/web_fcm.py` | Web Push credentials |
| `SENTRY_DSN` | `utils/fcm_observability.py` | FCM anomalies are reported through `sentry_sdk` |
| `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_CUSTOM_DOMAIN` | `storage_config.py` | Cloudflare R2 media backend |
| `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE` | Upload pipeline | Limits applied before background processing |

**Cloudflare R2** is wired here: `storage_config.py` exposes `r2_media_storage_enabled()` and
`build_r2_default_storage()`, and `settings.py` only activates the S3 backend when the environment is
production, `TEST_ENVIRONMENT` is off, and every R2 credential is present. Media is then served from
`https://{R2_CUSTOM_DOMAIN}/media/` with `querystring_auth=False`. Static files do **not** go to R2 —
they use `ManifestStaticFilesStorage` and are served by Nginx.

External dependencies: Redis, Celery, ffmpeg, Pillow, PyMuPDF, `firebase-admin` / `pywebpush`,
`django-storages` + `boto3`. Container-level configuration for all of these is documented in
[`docs/docker.md`](../../docs/docker.md).

Management commands: `clean_old_notifications`, `clear_push_subscriptions`.
