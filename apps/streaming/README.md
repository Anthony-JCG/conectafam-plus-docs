# streaming

## Description

Live-session management. A user configures a stream with a waiting page, a public viewer page, and a
post-finalisation page used to convert attendees into contacts. Video is served as HLS, transcoded
in the background rather than streamed in real time.

Relationship to the core apps:

- **`user_levels`** — creation limits and visibility (`check_action_allowed`,
  `get_model_visible_queryset`, `collect_downgrade_blocks`). This app implements the **PRO
  derivative** rule: a PRO user may create a derivative stream (`parent_stream`) from an upline
  original through `use_shared_stream`; the derivative is personal while the original stays the
  shared source for the line.
- **`core`** — file processing, the HLS transcoding Celery task, Redis wrappers, and constants
  (`MAX_SIMULTANEOUS_STREAMS`, `MAX_VIEWERS_PER_STREAM`).
- **`users.User`** — owns every stream.
- **`communication`** — registered viewers become `Contact` rows, and the post-finalisation page
  links to a `WhatsAppLink`.

## Models and Data

| Model | Relationships |
|---|---|
| `Streaming` | FK → `users.User`; FK → `self` (`parent_stream`, PRO derivatives). Holds `video_file`, `hls_manifest`, `is_processing`, scheduling data |
| `PostFinalizationPage` | OneToOne → `Streaming`; FK → `communication.WhatsAppLink` (`link_whatsapp`) |
| `SliderImage` | FK → `PostFinalizationPage` |

Video handling: saving a `Streaming` with a new `video_file` enqueues `core.tasks.process_video_task`,
which runs ffmpeg to produce the HLS manifest and flips `is_processing`. A `post_delete` signal
removes the generated HLS tree from `default_storage`.

Viewer counting uses two layers: a Redis counter for the displayed number, and a Django cache set
keyed by session/IP for the real attendee list.

There is no `services.py` or `utils.py`; logic lives in `views.py`, `forms.py`, and `tasks.py`
(scheduled reminder emails, enqueued from `views._schedule_stream_emails`).

## Views and Frontend Integration

**This app does not use HTMX.** Forms post normally and the live counters poll JSON endpoints from
`static/js/stream-page.js` and `streaming_modal.js`.

URL prefix: **`/streaming/`**

| URL | View | Response |
|---|---|---|
| `waiting-page/` | `waiting_page` | Stream management panel (HTML) |
| `stream-page/<user_id>_<stream_id>/` | `stream_page` | Public stream page, or the post-finalisation page once ended (HTML) |
| `preview/stream/<id>/` · `preview/post-page/<id>/` | `stream_page_preview`, `post_page_preview` | Owner-only previews (HTML) |
| `save-waiting-page/` | `save_waiting_page` | Creates/updates the stream (redirect) |
| `save-post-finalization-page/` | `save_post_finalization_page` | Post-finalisation page CRUD (redirect) |
| `delete-streaming/` | `delete_streaming` | Deletes the stream (redirect) |
| `register-stream-viewer/` | `register_stream_viewer` | Registers a viewer as a contact (JSON) |
| `join-stream/` · `leave-stream/` · `get-stream-viewers/` | `join_stream`, `leave_stream`, `get_stream_viewers` | Live viewer counters (JSON) |
| `copy/<id>/` | `copy_stream` | Copies a visible stream (redirect) |
| `use-shared-stream/` | `use_shared_stream` | Creates the PRO derivative from an upline original (redirect) |

## Configuration and Dependencies

| Setting | Purpose |
|---|---|
| `FFMPEG`, `FFPROBE` | HLS transcoding, executed by `core.tasks.process_video_task` |
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Viewer counters |
| `R2_*` / `STORAGES` | Source videos and generated HLS segments live on the media backend (Cloudflare R2 in production) |
| `MAX_SIMULTANEOUS_STREAMS`, `MAX_VIEWERS_PER_STREAM` (from `core.const`) | Application-wide caps |
| Email (SMTP) settings | Scheduled reminder emails sent from `tasks.py` |

External services: Redis, Celery (reminder emails and video transcoding), ffmpeg. **No Sentry or
Stripe integration** in this app.

Serving HLS from Cloudflare R2 depends on the global media configuration described in
[`apps/core/README.md`](../core/README.md); container-level ffmpeg availability and Celery worker
setup are documented in [`docs/docker.md`](../../docs/docker.md).

App dependencies: `communication`, `core`, `main` (`notifications_texts`), `user_levels`, `users`.
