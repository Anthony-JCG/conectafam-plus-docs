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
| `Board` | User container: title, cover image, order, `share_token`, `allow_duplicate_on_share`, `is_public`, `is_client_area`. FK → `users.User` |
| `BoardFolder` | Nestable folders (`parent` FK → self), sortable in the mosaic. Optional `catalog_folder` FK → `BoardFolder` for client-area shadow folders |
| `BoardItem` | Mosaic element. Types: `text`, `image`, `link`, `video`, `voice`, `pdf`, `youtube`, `page`. Files up to 10 MB. Optional FK → `landing.LandingPage` |
| `BoardCollaborator` | Invited user. PRO+ collaborators have read+edit access; Basic collaborators are view-only. Unique on `(board, user)` |
| `BoardLibraryEntry` | Reference to a shared board saved into the user's own library (read-only) |
| `BoardDeleteLog` | Append-only log of permanently deleted boards. `board_id` / `user_id` are plain integers because the `Board` row is already gone. Consumed **only** by the keyboard API delta-sync endpoint so mobile clients know what to purge |

### Client-area boards

Two boards carry `is_client_area=True`; an advisor only ever sees **one**, "Área de clientes":

| Board | Owner | Allowed item types | Created by |
|---|---|---|---|
| System catalog (`CLIENT_AREA_CATALOG_TITLE`, folders Nutrición / Deporte / Videoteca / Otros) | FAM TEAM / `USER_ROOT` | PDF, image (`CLIENT_AREA_CATALOG_ITEM_TYPES`); Videoteca also uploaded video and YouTube (`CLIENT_AREA_CATALOG_FOLDER_EXTRA_ITEM_TYPES`) | Migrations `0009` / `0010`; `manage.py seed_client_area_board` (idempotent) |
| Own client-area board ("Área de clientes", `CLIENT_AREA_OWN_BOARD_TITLE`) | Each entitled advisor, private | Folders, text, image, PDF, uploaded video, YouTube (`CLIENT_AREA_OWN_ITEM_TYPES`) | `client_area_catalog.ensure_user_client_area_board` on first use (boards home, client-area pane) |

Only `USER_ROOT` edits the catalog, and `USER_ROOT` sees nothing else. Advisors manage their own
board with the regular board views.

#### Merged view

The own board is the advisor's single entry point (boards home, search, client-area picker).
`client_area_catalog.get_merged_catalog_board(user, board)` returns the catalog when `board` is the
user's own client-area board, and the view merges both:

| Location | Tiles |
|---|---|
| Board root | Only the catalog folders (read-only) |
| Catalog folder | Root's tiles (read-only), then the tiles of the advisor's shadow folder |
| Own folder | Own tiles |

- `utils.build_view_mosaic_tiles` adds `read_only: true` to catalog tiles *after* reading the
  cache. Each underlying board keeps its own mosaic Redis entry (board/folder), so the cache never
  holds per-user data.
- `utils.find_view_folder` / `utils.get_view_item` resolve catalog folders and items under the own
  board URL (`board_folder`, `board_mosaic_data`, `board_item_tile`). Files are still served by
  `board_item_file` on the catalog board (tiles carry its URL).
- `board_detail` on the catalog redirects an advisor to their own board (same folder and query
  string, e.g. `open_item` from search). The search index lists catalog folders and items as
  read-only tiles, but no catalog board entry.
- `mosaic.js` doesn't drag or select read-only tiles (the client-area picker still selects them)
  and leaves them out of the reorder payload; `item-viewer.js` hides edit, move and delete for
  them.

#### Root lock

Nothing is added at the root of a client-area board, neither by root nor by advisors: its root
only holds the catalog folders (Nutrición / Deporte / Videoteca / Otros), and content goes inside
them (or their subfolders).

- UI: `utils.build_board_detail_context` sets `can_add`, so `board-detail.html` hides "Añadir" at
  the root; `folder_options` has no "Raíz del board" entry on these boards.
- Server: `client_area_root_locked(board, folder)` makes `save_board_folder` (create),
  `save_board_item` (create), `move_board_item` and bulk move answer
  `CLIENT_AREA_ROOT_LOCKED_MESSAGE` when the target folder is the root. Edits keep the item's
  folder.
- The allowed item types depend on the folder: `client_area_root_folder(folder)` walks up to the
  root folder (a shadow folder maps to its catalog folder) and `client_area_item_types(board,
  folder)` adds its `CLIENT_AREA_CATALOG_FOLDER_EXTRA_ITEM_TYPES`. `item-modal.js` sends
  `folder_id` to `load_board_item_form` so the type menu matches the folder.

Own top-level folders created before this rule are no longer valid; migration `0012` moves loose
root content into Otros.

#### Shadow folders

Advisors can add items and subfolders inside root's folders; the catalog folder itself stays
read-only (no rename or delete: `is_catalog_folder` hides those actions).

- The content lives in a *shadow folder* of the own board: `BoardFolder.catalog_folder` (nullable
  FK, one per board and catalog folder) points at the catalog folder.
- `client_area_catalog.ensure_shadow_folder` creates it on the first write, through
  `utils.find_write_folder` / `get_write_folder` (used by `save_board_item`, `save_board_folder`,
  `move_board_item` and bulk move): a catalog folder id sent to the own board maps to its shadow.
- Shadow folders sit at the own board root, which the merged view never lists (it shows only the
  catalog folders). Opening one by id shows its catalog folder, move options label it with the
  catalog title, and the search index lists its items (URL `board_folder(own, shadow)`) without a
  folder entry of its own.
- If root deletes the catalog folder, `SET_NULL` turns the shadow into a regular folder, so nothing
  is lost.

Writes stay scoped to the board in the URL: save, delete, move, reorder and bulk actions look items
and folders up with `board=board`, so a catalog item id sent through the own board is a 404 or is
ignored. Items never move between the two boards.

Two boards behind one view, rather than an owner per item, because every board service (mosaic
cache, search index, `board_item_file`, bulk operations, reorder) is scoped by board: a private
board reuses the whole item CRUD with one nullable FK and no per-item ownership checks, and merging
only happens when reading.

#### Permissions

All in `services/board_permissions.py`; entitlement is `user_levels`
`check_action_allowed(CLIENT_AREA_MODEL_KEY, ACCESS_ACTION_KEY)` or the `client_area` add-on.

| Function | Rule |
|---|---|
| `user_can_view_client_area_board` | Own board, or the system catalog while entitled; never another advisor's board. Library entries, collaborators and share links never apply (`board_share`, `save_shared_board` and `resolve_board_read_access` ignore client-area boards) |
| `user_can_manage_board_collaborators` | Always `False` for client-area boards |
| `user_can_edit_board` | Owner only: `USER_ROOT` for the catalog, the entitled advisor for their own board |
| `user_may_write_board_content` | Skips the plan write routes for client-area boards; `RouteLevelAccessMiddleware` (`CLIENT_AREA_BOARD_WRITE_ROUTES`) lets a Basic user with the add-on use them on their own board only |
| `get_client_area_catalog_boards_queryset(user)` | System catalog first, then the own board. Used by the search index and the client-area picker search and forms |
| `client_area_item_types(board, folder)` / `board_allows_item_type` / `require_client_area_item_type` | Allowed types per board and root folder (Videoteca adds video and YouTube); also drive the "Añadir" menu (`client_area_add_menu(board, folder)`) and `load_board_item_form` |
| `client_area_root_locked(board, folder)` | `True` at the root of a client-area board: no folder or item can be created or moved there |

The owner settings form exposes only title, description and cover; client-area boards cannot be
deleted from the UI (`delete_board` / `save_board` skip them). The flag also excludes them from
keyboard sync (`_get_accessible_board_ids`) and from `BOARDS_MODEL_KEY` create limits and
excess-object counts.

#### Migrations

| Migration | Change |
|---|---|
| `0009_seed_client_area_catalog_board` | Creates the catalog board and its folders for `USER_ROOT` if missing |
| `0010_set_client_area_catalog_cover` | Sets the default cover (`static/img/min_board.jpg`, stored as-is, no WebP) when the catalog has none |
| `0011_boardfolder_catalog_folder` | Adds `BoardFolder.catalog_folder` (shadow folders) |
| `0012_client_area_root_folders_only` | Data: creates any missing catalog root folder (Nutrición / Deporte / Videoteca / Otros) and moves folders and items at the root of a client-area board into Otros (the catalog's own folder, or the advisor's shadow folder of it) |

`0009`, `0010` and `0012` only use historical models (`apps.get_model`), so `0011` and later schema changes
apply cleanly after them on a fresh database. Both skip with a warning when `USER_ROOT` (or the
catalog board) doesn't exist yet; `seed_client_area_board` creates it later. `0010` fails if the
static cover is missing.

### Access logic

| User type | View | Edit | Manage | Duplicate |
|---|---|---|---|---|
| Owner | ✓ | ✓ | ✓ | ✓ |
| Collaborator (PRO+) | ✓ | ✓ | — | ✓ |
| Collaborator (Basic) | ✓ | — | — | ✓ |
| Library entry | ✓ | — | — | Only if `allow_duplicate_on_share` |
| Public board | ✓ | — | — | — |

### Plan-based permissions

| Level | Access | Creation limit | Share with team (`is_public`) |
|---|---|---|---|
| Basic | Read public/shared; view-only as collaborator | — | — |
| Pro | Yes | 1 | — |
| Leader | Yes | 3 | Yes, within its visibility bubble |
| Leader Pro | Yes | Unlimited | Yes, same bubble rules |

Restricted routes return 404 through `RouteLevelAccessMiddleware`. Basic-level collaborators
keep view access to the boards they collaborate on, but cannot write content. Managing
collaborators (add/remove) is a Leader / Leader Pro owner action; PRO owners see the section
behind a restricted-access overlay.

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
| `services/board_cover.py` | Reprocesses the board cover to WebP; assigns default covers from static |
| `services/item_titles.py` | Resolves item titles from external sources (YouTube, link metadata) |
| `services/voice_convert.py` | WebM → MP3 through ffmpeg; raises `VoiceConversionError` |
| `services/folder_options.py` | Folder options for the legacy move-modal dropdown; the destination picker loads folders on demand from the mosaic JSON endpoint |
| `services/client_area_catalog.py` | Client-area boards: ensure catalog / own board, merged catalog lookup, shadow folders |
| `services/client_area_uploads.py` | Content uploaded from the client-area pane becomes a board item: `get_client_area_upload_folder(user, root_title, subfolder_title)` (catalog folder for `USER_ROOT`, the shadow folder for an advisor; subfolder created on first use) and `create_client_area_item(folder, uploaded_file=, youtube_url=)` |
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
