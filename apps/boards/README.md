# boards

## Description

Per-user personal library. Organises resources into **boards** rendered as a mosaic (folders, files,
links, voice recordings, and pages powered by the landing engine). Supports link sharing, saving
another user's board read-only, collaborating with other users, and duplicating items according to
the owner's settings.

Relationship to the core apps:

- **`user_levels`** — creation limits (`BOARDS_MODEL_KEY`) and restricted routes. Every ACL decision
  in `services/board_permissions.py` ultimately calls `check_action_allowed` or
  `get_visible_creator_ids`; boards never reimplements level rules.
- **`core`** — `BaseForm`, file processing (`process_image_field_if_changed`), Redis wrappers, PDF
  thumbnails, share-preview URLs, and the `attach_toast_trigger` / `htmx_error_response` HTMX
  contract.
- **`users.User`** — owns `Board`, `BoardCollaborator`, and `BoardLibraryEntry`.
- **`landing`** — `page`-type items create and render a `LandingPage` with `page_context=board`.
- **`keyboard_api`** — board mutations enqueue Celery tasks that push silent FCM notifications to the
  mobile keyboard client.

## Models and Data

| Model | Responsibility |
|---|---|
| `Board` | User container: title, cover image, order, `share_token`, `allow_duplicate_on_share`, `is_public`. FK → `users.User` |
| `BoardFolder` | Nestable folders (`parent` FK → self), sortable in the mosaic |
| `BoardItem` | Mosaic element. Types: `text`, `image`, `link`, `video`, `voice`, `pdf`, `youtube`, `page`. Files up to 10 MB. Optional FK → `landing.LandingPage` |
| `BoardCollaborator` | Invited user with read+edit access. Unique on `(board, user)` |
| `BoardLibraryEntry` | Reference to a shared board saved into the user's own library (read-only) |
| `BoardDeleteLog` | Append-only log of permanently deleted boards. `board_id` / `user_id` are plain integers because the `Board` row is already gone. Consumed **only** by the keyboard API delta-sync endpoint so mobile clients know what to purge |

### Access logic

| User type | View | Edit | Manage | Duplicate |
|---|---|---|---|---|
| Owner | ✓ | ✓ | ✓ | ✓ |
| Collaborator | ✓ | ✓ | — | ✓ |
| Library entry | ✓ | — | — | Only if `allow_duplicate_on_share` |
| Public board | ✓ | — | — | — |

### Plan-based permissions

| Level | Access | Creation limit | Share with team (`is_public`) |
|---|---|---|---|
| Basic | Read public/shared; write only as collaborator | — | — |
| Pro | Yes | 1 | — |
| Leader | Yes | 3 | Yes, within its visibility bubble |
| Leader Pro | Yes | Unlimited | Yes, same bubble rules |

Restricted routes return 404 through `RouteLevelAccessMiddleware`. Basic-level collaborators keep
write access to the boards they collaborate on.

### Services

| Module | Function |
|---|---|
| `services/board_permissions.py` | ACL: ownership, collaboration, public visibility, duplication, level-based visibility |
| `services/board_collaborators.py` | `add_collaborator` / `remove_collaborator` with validation and cache invalidation |
| `services/board_items.py` | Creation of `page`-type items (spawns a `LandingPage`) and recursive item duplication with files |
| `services/board_cache.py` | Redis cache of the mosaic payload per board and folder (TTL 300 s) |
| `services/search_index.py` | Per-user Redis search index across own, collaborated, saved, and public boards |
| `services/bulk_operations.py` | Bulk delete, move, and duplicate with folder-tree support |
| `services/mosaic_preview.py` | Generates and syncs WebP tile thumbnails, including PDF first-page previews |
| `services/landing_page_preview.py` | Resolves preview URLs and embedded HTML for `page`-type items |
| `services/board_cover.py` | Reprocesses the board cover to WebP |
| `services/item_titles.py` | Resolves item titles from external sources (YouTube, link metadata) |
| `services/voice_convert.py` | WebM → MP3 through ffmpeg; raises `VoiceConversionError` |
| `services/folder_options.py` | Folder options for the legacy move-modal dropdown; the destination picker loads folders on demand from the mosaic JSON endpoint |
| `services/keyboard_sync.py` | Touches `updated_at` and enqueues the mobile-sync Celery task |
| `utils.py` | Board access resolution, mosaic payload, reordering, detail context |
| `link_meta.py`, `youtube.py` | Outbound fetches for Open Graph previews and YouTube oEmbed |

## Views and Frontend Integration

**This app uses HTMX**, but only for form submission — the mosaic itself stays a client-side Muuri
grid fed by JSON.

URL prefix: **`/boards/`**

### HTMX endpoints

| Endpoint | Name | HTMX behaviour |
|---|---|---|
| `<id>/item/form/` | `load_board_item_form` | GET partial → `components/partials/board-item-form-fields.html` |
| `save/` | `save_board` | `204` + **`HX-Redirect`** to the new board |
| `<id>/folder/save/` | `save_board_folder` | `HX-Trigger` toast via `attach_toast_trigger` |
| `<id>/item/save/` | `save_board_item` | `HX-Trigger` toast; `hx-encoding="multipart/form-data"` |
| `<id>/settings/` | `save_board_settings` | `HX-Trigger` toast |
| `<id>/page/<landing_id>/preview/` | `board_landing_page_preview` | Raw HTML fragment for the embedded landing preview |

Validation failures return `htmx_error_response` (422 + `HX-Trigger`). Submitting templates:
`components/modal-board.html`, `modal-board-folder.html`, `modal-board-item.html`,
`modal-board-settings.html`, all with `hx-post` + `hx-swap="none"` and `data-close-modal`.

### JSON and HTML endpoints

| Route | Name | Description |
|---|---|---|
| `""` | `boards_home` | Listing: own, collaborated, public, and library boards |
| `<id>/` · `<id>/folder/<folder_id>/` | `board_detail`, `board_folder` | Mosaic view |
| `<id>/mosaic/` | `board_mosaic_data` | JSON tile payload (Redis-cached) |
| `<id>/item/<item_id>/tile/` | `board_item_tile` | JSON for a single tile after editing |
| `<id>/item/<item_id>/file/` | `board_item_file` | Serves the file with an `inline` header |
| `<id>/item/delete/` · `move/` · `duplicate/` | `delete_board_item`, `move_board_item`, `duplicate_board_item` | Item mutations (JSON) |
| `<id>/folder/delete/` | `delete_board_folder` | Delete folder (JSON) |
| `<id>/bulk/delete/` · `move/` · `duplicate/` | `bulk_*_board` | Bulk selection operations (JSON) |
| `<id>/reorder/` | `reorder_board_mosaic` | Bulk tile ordering (JSON) |
| `<id>/collaborators/add/` · `remove/` | `add_board_collaborator`, `remove_board_collaborator` | Collaborator management (JSON) |
| `delete/` | `delete_board` | Delete board (JSON); writes a `BoardDeleteLog` row |
| `search-index/` | `board_search_index` | Per-user search index (JSON) |
| `link-meta/`, `youtube-meta/` | `board_link_meta`, `board_youtube_meta` | Outbound metadata lookups (JSON) |
| `share/<token>/` · `folder/<id>/` | `board_share`, `board_share_folder` | Shared view (login required) |
| `share/<token>/save/` | `save_shared_board` | Save into own library |
| `<username>/board_<id>/` | `board_page_template` | Public page for a `page`-type item |

### Frontend notes

Templates extend `base-main.html`. Board detail shows **Atrás** (parent folder or board root, only
inside a folder) and **Volver a Boards** instead of a breadcrumb trail; both are hidden on the share
view.

Toasts, busy state, and modal closing are handled by the global HTMX lifecycle in
`static/js/core.js` reacting to `data-close-modal` and `HX-Trigger`. Board-specific side effects
(mosaic reload, search reindex, page-item redirect) stay in `board-detail.js` / `board-home.js`,
bound on `htmx:afterRequest`.

The item modal reuses the shared shell `#formBoardItem-fields` + `#formBoardItem-fields-template`
wired through `htmx_modal_*` kwargs on `base-modal.html`. Field HTML is fetched by the global
`static/js/htmx_modal_form.js` from `load_board_item_form` (`item_id` when editing; creation passes
`item_type` plus a sentinel id so the loader issues a GET instead of restoring the empty template).
`BoardItemForm` shapes visible fields and `accept` per type; PDF editing prefers the stored
`mosaic_preview`. After settle, the `boards:item-form-loaded` event lets `item-modal.js` bind only
domain UX — YouTube/link blur previews, PDF filename helper, voice recorder. File previews come from
`fileUploadUtils.initPreviewsInScope`, not reimplemented here.

Modular JS in `static/js/`: `api`, `mosaic`, `item-modal`, `item-viewer`, `board-detail`,
`board-home`, `board-search`, `board_destination_picker`, `voice-recorder`, `pdf-preview`. Styles in
`static/css/boards.css`, which imports `boards-search`, `boards-tiles`, `boards-mosaic`, and
`boards-viewer`.

## Configuration and Dependencies

| Setting | Purpose |
|---|---|
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Mosaic cache and per-user search index |
| `FFMPEG`, `FFPROBE` | Voice recording conversion (WebM → MP3) |
| `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE` | Item uploads (10 MB cap enforced in the model) |
| `R2_*` | Item files and covers land on Cloudflare R2 through the global `STORAGES` backend configured by `core.storage_config` |

External services: Redis (cache and search index), Celery (mobile sync notifications via
`apps.keyboard_api.tasks`), ffmpeg, and outbound HTTP for Open Graph / YouTube oEmbed metadata and
Google favicons. **No direct Sentry integration** — errors surface through the global handler.

`apps/boards/signals.py` is registered from `apps.py` and fires the keyboard-sync tasks plus the
`BoardDeleteLog` bookkeeping.

Container-level configuration (ffmpeg availability, Redis service, Celery workers) is documented in
[`docs/docker.md`](../../docs/docker.md).
