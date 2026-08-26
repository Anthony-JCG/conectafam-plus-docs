# Keyboard API — Technical Reference

Backend API that powers the **mobile global keyboard** — a companion app to the Conectafam Plus
Boards module. The keyboard runs as an isolated, offline-capable extension. All data is stored
locally on the device; the keyboard reads only from that local store and never makes direct API
calls during use.

---

## Architecture Overview

```
┌────────────────────────────────────────────┐
│  Conectafam Plus Web (Django)               │
│                                            │
│  Board changes ──► Django Signals          │
│                         │                  │
│                         ▼                  │
│                  Firebase Admin SDK        │
│                         │                  │
└─────────────────────────┼──────────────────┘
                          │ Silent FCM push
                          ▼
┌─────────────────────────────────────────────┐
│  Mobile App (main process)                  │
│                                             │
│  On push received:  GET /api/keyboard/sync/ │
│  Stores result in App Group shared storage  │
└────────────────────┬────────────────────────┘
                     │ Local read only
                     ▼
┌────────────────────────────────────────────┐
│  Keyboard Extension (isolated process)     │
│  No network access / reads local storage   │
└────────────────────────────────────────────┘
```

### Design rationale

iOS and Android keyboard extensions are sandboxed processes with strict memory (~30–50 MB on iOS) and no guaranteed network access. Calling the API directly from within the extension is unreliable and violates platform security policies.

The chosen architecture separates concerns cleanly:

- **Initial sync** — on first login the main app downloads the full board snapshot and writes it to a shared container (App Group on iOS, shared storage on Android).
- **Incremental sync** — when any board, folder, or item changes on the web, Django Signals fire and the server sends a **silent Firebase push notification** to all registered devices of affected users. The main app receives it in the background, calls `GET /sync/`, and updates local storage.
- **Keyboard extension** — reads exclusively from local storage. No network dependency at use time.

---

## Sync Flow

```
── First login ──────────────────────────────────────────────────────────

1. POST /api/keyboard/auth/token/
   → store token securely (Keychain / Keystore)

2. POST /api/keyboard/auth/fcm-token/
   → register FCM device token

3. GET  /api/keyboard/sync/            (no ?since — full sync)
   → is_full_sync: true
   → store all boards + store synced_at value locally
   → keyboard extension now has complete offline data

── Normal use ───────────────────────────────────────────────────────────

4. [Web] User edits a board (any folder, item, or board metadata)
   → Django signal touches Board.updated_at
   → Celery task sends silent FCM push to affected devices

5. Main app receives FCM push  (data.event == "boards_changed")
   → GET /api/keyboard/sync/?since=<last synced_at>  (delta sync)
   → is_full_sync: false
   → upsert changed boards into local store
   → remove deleted_board_ids from local store
   → update stored synced_at to the new value

── keyboard extension reads only from local storage ─────────────────────
```

---

## Base URL

| Environment | Base URL |
|---|---|
| Production | `https://conectafam-plus.com/api/keyboard/` |
| Local dev (`runserver`) | `http://localhost:8000/api/keyboard/` |
| Local dev (Docker) | `http://localhost:${WEB_PORT}/api/keyboard/` — Nginx fronts Gunicorn, which binds `:8080` inside the container. See [`docs/docker.md`](../../docs/docker.md) |

---

## Authentication

The API uses **token-based authentication** (no session cookies, no CSRF). Every protected endpoint requires:

```
Authorization: Token <token>
```

Tokens are 64-character hex strings (256 bits of entropy via `secrets.token_hex(32)`). One token exists per `(user, device_id)` pair — a single user may be authenticated on multiple devices simultaneously. Tokens are persistent; use the refresh endpoint for security rotation.

---

## Endpoints

### 1. Obtain Token

**`POST /api/keyboard/auth/token/`**

Authenticates with platform credentials and returns a persistent device token. No `Authorization` header required.

#### Request body (JSON)

```json
{
  "username": "string",
  "password": "string",
  "device_id": "string",
  "device_name": "string"
}
```

| Field | Required | Description |
|---|---|---|
| `username` | Yes | Conectafam Plus username |
| `password` | Yes | Conectafam Plus password |
| `device_id` | Yes | Stable UUID generated on first install; stored in Keychain / Keystore |
| `device_name` | No | Human-readable label shown in admin (e.g. `"iPhone 15 Pro"`) |

#### Responses

| Status | Description | Body |
|---|---|---|
| `200 OK` | Token issued | `{"token": "...", "user_id": 42, "username": "johndoe"}` |
| `400 Bad Request` | Malformed JSON or missing `device_id` | `{"error": "..."}` |
| `401 Unauthorized` | Wrong credentials | `{"error": "Invalid credentials."}` |
| `403 Forbidden` | Account lacks keyboard API access | `{"error": "Your account does not have access to this API."}` |
| `429 Too Many Requests` | IP rate limit exceeded | `{"error": "Too many failed attempts. Try again later."}` |

**Rate limiting:** 10 failed attempts per IP within a 10-minute window (Redis-backed).

---

### 2. Refresh Token

**`POST /api/keyboard/auth/token/refresh/`**

Rotates the current token, invalidating the old one. Use for periodic security rotation.

#### Request headers

```
Authorization: Token <current_token>
```

No request body required.

#### Responses

| Status | Description | Body |
|---|---|---|
| `200 OK` | New token issued | `{"token": "...", "user_id": 42, "username": "johndoe"}` |
| `401 Unauthorized` | Missing or invalid token | `{"error": "Invalid or expired token."}` |

---

### 3. Register FCM Token

**`POST /api/keyboard/auth/fcm-token/`**

Stores or updates the Firebase Cloud Messaging registration token for this device. The server uses it to deliver silent sync push notifications when board data changes.

Call this endpoint:
- Immediately after a successful login (`obtain_token`).
- Whenever the OS rotates the FCM token (the FCM SDK provides an `onTokenRefresh` / `didReceiveRegistrationToken` callback for this event).

#### Request headers

```
Authorization: Token <token>
Content-Type: application/json
```

#### Request body (JSON)

```json
{"fcm_token": "string"}
```

#### Responses

| Status | Description | Body |
|---|---|---|
| `200 OK` | FCM token saved | `{"status": "ok"}` |
| `400 Bad Request` | Missing or empty `fcm_token` | `{"error": "fcm_token is required."}` |
| `401 Unauthorized` | Missing or invalid token | `{"error": "..."}` |
| `503 Service Unavailable` | Firebase not initialised on server | `{"error": "Push notification service unavailable."}` |

---

### 4. Boards Sync (full and delta)

**`GET /api/keyboard/sync/`** — full sync (first login)
**`GET /api/keyboard/sync/?since=<ISO8601>`** — delta sync (subsequent updates)

The same endpoint handles both modes. The presence of the `since` parameter selects the mode.

**Never** call this endpoint from within the keyboard extension itself — only the main app process should call it, then write the result to App Group / shared storage.

#### Query parameters

| Param | Required | Description |
|---|---|---|
| `since` | No | ISO 8601 datetime with timezone — the `synced_at` value from the previous response. Omit for a full sync. |

#### Request headers

```
Authorization: Token <token>
```

#### Responses

| Status | Description | Body |
|---|---|---|
| `200 OK` | Sync payload | `SyncResponse` (see Data Structures) |
| `400 Bad Request` | Unparseable `since` value | `{"error": "Invalid 'since' parameter. ..."}` |
| `401 Unauthorized` | Missing or invalid token | `{"error": "..."}` |
| `500 Internal Server Error` | Unexpected error | `{"error": "Internal server error."}` |

#### Full sync performance (no `since`)

| Query | What it fetches |
|---|---|
| 4 ID lookups | Owned, library, collaborator, and public board IDs |
| 1 board query | All Board rows with owner (`select_related`) |
| 1 folder query | All BoardFolder rows (bulk) |
| 1 item query | All BoardItem rows with landing page (bulk, `select_related`) |

#### Delta sync performance (`?since=`)

| Query | What it fetches |
|---|---|
| 4 ID lookups | Same access resolution as full sync |
| 1 changed-IDs query | Board IDs with `updated_at > since` |
| 1 board query | Only the changed Board rows |
| 1 deletion query | `BoardDeleteLog` entries with `deleted_at > since` |
| 1 folder query | Only folders of changed boards |
| 1 item query | Only items of changed boards |

For a typical edit (one board changed), queries 5–6 return a single row each. Payload size is proportional to what actually changed.

#### Delta sync limitation

`deleted_board_ids` covers only permanent board deletions. Boards that become inaccessible due to a permission change (e.g. owner revokes public access, collaborator is removed) are **not** included. Handle this by performing a full sync periodically (e.g. once per day or on explicit user pull-to-refresh) so stale boards are purged from the local store.

---

### 5. List Boards (progressive navigation)

**`GET /api/keyboard/boards/`**

Returns a lightweight list of boards without folders or items. Available as an alternative to the full sync for cases where only the board list is needed.

#### Request headers

```
Authorization: Token <token>
```

#### Responses

| Status | Description | Body |
|---|---|---|
| `200 OK` | Success | `{"boards": [BoardSummary, ...]}` |
| `401 Unauthorized` | Missing or invalid token | `{"error": "..."}` |
| `500 Internal Server Error` | Unexpected error | `{"error": "Internal server error."}` |

---

### 6. Get Board Content (one level)

**`GET /api/keyboard/boards/<board_id>/`**

Returns folders and items for one folder level. Omit `folder_id` for the board root; pass it to drill into a subfolder.

#### Request headers

```
Authorization: Token <token>
```

#### Query parameters

| Param | Required | Description |
|---|---|---|
| `folder_id` | No | Folder to open; omit for board root |

#### Responses

| Status | Description | Body |
|---|---|---|
| `200 OK` | Success | `BoardContentResponse` |
| `400 Bad Request` | Invalid `folder_id` | `{"error": "Invalid folder_id."}` |
| `401 Unauthorized` | Missing or invalid token | `{"error": "..."}` |
| `404 Not Found` | Board/folder not found or no access | `{"error": "Board not found."}` |
| `500 Internal Server Error` | Unexpected error | `{"error": "Internal server error."}` |

---

## Data Structures

### FullBoard (from `GET /sync/`)

```json
{
  "id": 1,
  "title": "Marketing Resources",
  "description": "Links and files for the marketing team.",
  "cover_image": "https://conectafam-plus.com/media/boards/covers/cover.jpg",
  "url": "https://conectafam-plus.com/boards/1/",
  "order": 0,
  "updated_at": "2026-06-25T22:00:00.000000+00:00",
  "owner_username": "johndoe",
  "is_owner": true,
  "is_library": false,
  "is_collaborator": false,
  "is_public": false,
  "folders": [FolderSummary],
  "items": [ItemObject]
}
```

`folders` contains **all** folders of the board (not just root-level). `items` contains **all** items of the board across all folders. Both are flat lists; the client reconstructs the tree using `parent_id` on folders and `folder_id` on items.

- `folder.parent_id = null` → root-level folder
- `item.folder_id = null` → root-level item (not inside any folder)
- `item.folder_id = 5` → item belongs to folder with `id: 5`
- `url` → absolute web URL for the board detail page (`/boards/<id>/`)

### BoardSummary (from `GET /boards/`)

```json
{
  "id": 1,
  "title": "Marketing Resources",
  "description": "Links and files for the marketing team.",
  "cover_image": "https://conectafam-plus.com/media/boards/covers/cover.jpg",
  "url": "https://conectafam-plus.com/boards/1/",
  "order": 0,
  "updated_at": "2026-06-25T22:00:00.000000+00:00",
  "owner_username": "johndoe",
  "is_owner": true,
  "is_library": false,
  "is_collaborator": false,
  "is_public": false
}
```

### BoardContentResponse (from `GET /boards/<id>/`)

```json
{
  "board": {"...BoardSummary fields..."},
  "folder_id": null,
  "folders": [FolderSummary],
  "items": [ItemObject]
}
```

| Field | Type | Description |
|---|---|---|
| `board` | `BoardSummary` | Board metadata (includes `updated_at`) |
| `folder_id` | `int \| null` | Currently open folder (`null` = board root) |
| `folders` | `FolderSummary[]` | Direct child folders at this level only |
| `items` | `ItemObject[]` | Items at this level only |

### FolderSummary

```json
{
  "id": 5,
  "kind": "folder",
  "parent_id": null,
  "title": "Sales Scripts",
  "order": 0
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Folder primary key |
| `kind` | `"folder"` | Always `"folder"` |
| `parent_id` | `int \| null` | Parent folder ID, or `null` for root-level folders |
| `title` | `string` | Folder display name |
| `order` | `int` | Sort position within parent |

### Item Object

```json
{
  "id": 42,
  "kind": "item",
  "folder_id": null,
  "item_type": "voice",
  "title": "Sales intro",
  "display_title": "Sales intro",
  "text_content": "",
  "url": "",
  "file_url": "https://conectafam-plus.com/media/boards/files/recording",
  "file_name": "recording",
  "file_mime_type": "audio/mpeg",
  "share_url": "https://conectafam-plus.com/media/boards/files/recording",
  "preview_url": "",
  "youtube_video_id": "",
  "landing_page_id": null,
  "order": 1
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Item primary key |
| `kind` | `"item"` | Always `"item"` |
| `folder_id` | `int \| null` | Folder this item belongs to; `null` = root item |
| `item_type` | `string` | See Item Types table |
| `title` | `string` | Raw title as stored (may be empty) |
| `display_title` | `string` | Resolved display title — never empty |
| `text_content` | `string` | Full text for `text` items; empty for others |
| `url` | `string` | External URL for `link` and `youtube` items |
| `file_url` | `string` | Absolute URL to the media file |
| `file_name` | `string` | Filename as stored on the server (e.g. `"recording.m4a"`). Use as suggested filename when downloading or sharing. Empty if the item has no file. |
| `file_mime_type` | `string` | MIME type inferred from the filename extension, with per-type fallbacks for files stored without an extension (e.g. `"audio/mpeg"` for `voice`, `"video/mp4"` for `video`). Empty if the item has no file. |
| `share_url` | `string` | Best URL to paste or share this item externally |
| `preview_url` | `string` | Thumbnail or preview image URL |
| `youtube_video_id` | `string` | Extracted YouTube video ID, or `""` |
| `landing_page_id` | `int \| null` | Linked landing page ID, or `null` |
| `order` | `int` | Sort position within its parent |

#### Item Types

| `item_type` | Description | Populated fields |
|---|---|---|
| `text` | Plain text snippet | `text_content` |
| `image` | Uploaded image | `file_url`, `file_name`, `file_mime_type`, `preview_url` |
| `link` | External web link | `url`, `share_url` |
| `video` | Uploaded video | `file_url`, `file_name`, `file_mime_type` |
| `voice` | Voice recording | `file_url`, `file_name`, `file_mime_type` |
| `pdf` | PDF document | `file_url`, `file_name`, `file_mime_type` |
| `youtube` | YouTube video | `url`, `youtube_video_id`, `preview_url` |
| `page` | Landing page | `landing_page_id`, `share_url`, `preview_url` |

#### Preview URL notes

- `image`: pre-generated 480 px WebP thumbnail (`mosaic_preview`). Falls back to the raw file URL for items uploaded before thumbnail generation was introduced.
- `pdf`: pre-generated 480 px WebP thumbnail of the first page (`mosaic_preview`). Empty string if not yet generated.
- `youtube`: standard thumbnail (`https://i.ytimg.com/vi/{video_id}/hqdefault.jpg`)
- `page`: banner image from the landing page, if set
- `link`: **not populated** — fetch link previews client-side to avoid outbound HTTP during sync
- All other types: empty string

> The `mosaic_preview` thumbnails are generated server-side (PIL for images, PyMuPDF for PDFs) at upload time. No client-side resizing or PDF rendering is required.

### SyncResponse

```json
{
  "boards": [FullBoard],
  "deleted_board_ids": [42, 71],
  "synced_at": "2026-06-24T17:30:00.123456+00:00",
  "is_full_sync": false
}
```

| Field | Type | Description |
|---|---|---|
| `boards` | `FullBoard[]` | Changed/new boards with all folders and items. On full sync, contains every accessible board. On delta sync, contains only boards with `updated_at > since`. |
| `deleted_board_ids` | `int[]` | IDs of permanently deleted boards since `since`. Always `[]` on full sync. Client must remove these from local storage. |
| `synced_at` | `string` | UTC ISO 8601 timestamp. **Store this value and pass it as `since` on the next sync call.** |
| `is_full_sync` | `bool` | `true` on full sync (client replaces all local boards). `false` on delta (client upserts `boards` and removes `deleted_board_ids`). |

#### Client merge rules

- **Full sync (`is_full_sync: true`)**: Replace the entire local board store with `boards`.
- **Delta sync (`is_full_sync: false`)**:
  1. For each board in `boards`: upsert it in the local store (replace if exists, insert if new).
  2. For each ID in `deleted_board_ids`: remove the matching board from local storage.
  3. Update stored `synced_at` to the new value.

#### Client processing guide

The main app owns all network I/O. The keyboard extension must never call the API.

**Local store structure**

Persist at minimum:

| Key | Type | Purpose |
|---|---|---|
| `boards` | `FullBoard[]` | Full offline copy keyed by board `id` |
| `synced_at` | ISO 8601 string | Last successful sync timestamp — pass as `?since=` on delta sync |
| `auth_token` | string | Per-device API token (Keychain / Keystore) |
| `fcm_token` | string | Registered with `POST /auth/fcm-token/` |

Each `FullBoard` upsert replaces the entire board record (metadata + all folders + all items). Do not attempt field-level patching inside a board — the server always sends the complete board subtree on change.

**When to full-sync vs delta-sync**

| Trigger | Endpoint | Client action |
|---|---|---|
| First login | `GET /sync/` | Replace entire local store; save `synced_at` |
| FCM `boards_changed` | `GET /sync/?since=<synced_at>` | Upsert `boards`; remove `deleted_board_ids`; save new `synced_at` |
| App foreground after >24 h idle | `GET /sync/` | Full sync — purges boards lost due to permission changes |
| User pull-to-refresh | `GET /sync/` | Full sync |
| New device login (same user) | `GET /sync/` | Full sync on that device |
| After saving a public board in web (other tab/device) | Wait for FCM or foreground full sync | Public boards are not push-discovered individually (see below) |

**FCM handler (main app process only)**

```
onBackgroundMessage / didReceiveRemoteNotification:
  if data["event"] != "boards_changed":
    return
  token = loadAuthToken()
  since = loadSyncedAt()          // omit if null → full sync
  response = GET /sync/?since=since  (Authorization: Token …)
  if response.is_full_sync:
    replaceLocalBoards(response.boards)
  else:
    upsertBoards(response.boards)
    removeBoards(response.deleted_board_ids)
  saveSyncedAt(response.synced_at)
  notifyKeyboardExtension()       // App Group / shared prefs write complete
```

**Upsert algorithm (delta)**

For each board in `response.boards`:

1. If board `id` exists locally → delete old folders/items and replace with incoming payload.
2. If board `id` is new → insert entire board.
3. Rebuild any in-memory indexes (folder tree, item lookup by `id`).

For each `id` in `response.deleted_board_ids`:

1. Remove board `id` from local store.
2. Remove any cached media files tied exclusively to that board (optional cleanup).

**Board visibility after sync**

Use the access flags on each board to drive UI labels only — they do not affect merge logic:

| Flag | Meaning |
|---|---|
| `is_owner` | User created this board |
| `is_library` | User saved it via share link |
| `is_collaborator` | User was added as collaborator |
| `is_public` | Visible because `is_public = true` on the server |

A board may have multiple flags (e.g. owner + public).

**Preview fields**

- `preview_url` on items is server-generated and safe to cache locally.
- For `page` items, `preview_url` reflects the linked landing page banner/profile image. When the landing page title or images change on the web, the server regenerates the item thumbnail and includes the updated board in the next delta.
- For `link` items, `preview_url` is always empty — resolve previews client-side if needed.

**Permission-change edge cases**

Delta sync cannot detect boards that became inaccessible (collaborator removed, board made private, entry removed from library). Those boards remain in local storage until a full sync. Schedule a full sync on app foreground after extended idle time to purge stale entries.

Public boards created by other users are never individually push-notified (fan-out to all authenticated users is not scalable). They appear on the next full sync.

---

## Board Visibility Rules

The API returns all boards the user is allowed to see, applying the same rules as Conectafam Plus web:

1. **Owned** — boards created by the user
2. **Library** — boards saved via `BoardLibraryEntry`
3. **Collaborated** — boards where the user is a `BoardCollaborator`
4. **Public** — boards with `is_public = True`, visible to all authenticated users

The `is_owner`, `is_library`, `is_collaborator`, and `is_public` flags reflect all applicable categories for each board.

---

## Firebase Integration

### Server-side setup

Firebase Admin SDK is initialised in `apps/core/apps.py` (the `CoreConfig.ready()` hook). It reads credentials from the `FIREBASE_CREDENTIALS_JSON` environment variable (a JSON string). If the variable is absent or invalid, Firebase silently skips initialisation and no push notifications are sent.

### Push notification flow

Server-side changes enqueue a Celery task that sends one silent FCM push per affected board change. The signal handlers in `apps/boards/signals.py` only dispatch tasks — the FCM HTTP call never runs in the web request cycle.

#### Sync trigger matrix

| Event | Signal / hook | `Board.updated_at` bumped | FCM recipients |
|---|---|---|---|
| Board metadata created/updated | `post_save(Board)` | Yes (auto_now on save) | Owner, library users, collaborators |
| Folder created/updated/deleted | `post_save/post_delete(BoardFolder)` | Yes (SQL update) | Owner, library users, collaborators |
| Item created/updated/deleted | `post_save/post_delete(BoardItem)` | Yes (SQL update) | Owner, library users, collaborators |
| Item file upload + mosaic preview | `BoardItem.save()` (single notify) | Yes | Same — second internal save is suppressed |
| Mosaic reorder (bulk) | `apply_mosaic_reorder()` | Yes | Same |
| Landing page title/image change (board context) | `LandingPage.save()` → `sync_board_page_item_previews()` | Yes | Same |
| Landing block editor save (board context) | `landing_blocks._sync_board_page_previews_if_needed()` | Yes | Same |
| Collaborator added | `post_save(BoardCollaborator)` | Yes | Owner, library users, collaborators (includes the new collaborator) |
| Board saved to library | `post_save(BoardLibraryEntry)` | Yes | Owner, library users, collaborators (includes the saving user's devices) |
| Board permanently deleted | `post_delete(Board)` | N/A | Owner only (see deletion note below) |

**Not push-notified (require full sync on client):**

- New public boards from other users — discovered on next full sync.
- Access revoked (collaborator removed, board made private, library entry removed) — stale board purged on full sync.
- Library/collaborator devices on board deletion — owner notified immediately; others reconcile on next sync.

The Celery task (`apps/keyboard_api/tasks.py`):

1. Collects the FCM tokens of all devices belonging to the board owner, library users, and collaborators.
2. Sends a `MulticastMessage` with `data: {"event": "boards_changed"}`.
3. Uses `content_available: true` (iOS) and `priority: high` (Android) to trigger a background fetch without a visible alert.
4. Logs any per-token failures but never raises.

#### Board deletion and eventual consistency

When a board is deleted, Django cascade-deletes `BoardLibraryEntry` and `BoardCollaborator` rows in the same transaction. By the time `post_delete` fires, those rows are gone, so the task can only notify the board owner's devices directly. Library and collaborator devices are **not immediately notified**.

This resolves naturally: the next time any other board change triggers a sync push for those users, their `GET /sync/` response will simply not include the deleted board, and their local store will be updated. No special client-side handling is required — a full snapshot never contains stale boards.

### Client-side handling

The main app must implement a background notification handler that:

1. Checks `data["event"] == "boards_changed"`.
2. Calls `GET /api/keyboard/sync/` with the stored token.
3. Writes the response to the App Group shared container.

The keyboard extension reads from that shared container on open; it never initiates network requests.

### `firebase_required` decorator

Any view that depends on Firebase being available is decorated with `@firebase_required`:

```python
@csrf_exempt
@require_POST
@token_required
@firebase_required
def register_fcm_token(request):
    ...
```

If Firebase is not initialised, the decorator returns `503 Service Unavailable` before the view body executes, avoiding a `NameError` or silent no-op inside the view.

---

## Security

| Control | Implementation |
|---|---|
| **Transport security** | HTTPS terminated and enforced by Nginx in production. Django defines no `SECURE_SSL_REDIRECT` or HSTS settings — TLS is entirely an infrastructure concern ([`docs/docker.md`](../../docs/docker.md)) |
| **Authentication** | Token-based, 256-bit entropy (`secrets.token_hex(32)`), one token per device |
| **Brute force protection** | IP-based rate limiting on `/auth/token/` (10 attempts / 10 min, Redis) |
| **Token rotation** | `POST /auth/token/refresh/` for on-demand rotation |
| **CSRF** | Not applicable — `Authorization` header, no cookies |
| **Sensitive data** | Credentials never logged; error messages do not reveal username existence |
| **Access control** | `check_keyboard_api_access(user)` gate on every protected endpoint |
| **Inactive accounts** | Tokens for `is_active=False` users are rejected at auth time |
| **Firebase availability** | `@firebase_required` prevents views from executing when SDK is not initialised |

---

## Future: Per-Level Access Restrictions

Access is currently **not** level-restricted: `check_keyboard_api_access(user)` in
`apps/keyboard_api/auth.py` returns `user.is_active`. `KEYBOARD_API_MODEL_KEY = "keyboard_api"` is
already reserved in `apps/user_levels/const.py`; `KEYBOARD_ACCESS_ACTION_KEY` does not exist yet.

**Step 1.** Add `KEYBOARD_ACCESS_ACTION_KEY = "access"` to `apps/user_levels/const.py`.

**Step 2.** Add capabilities to `DEFAULT_LEVELS` in `apps/user_levels/capabilities.py`:
```python
KEYBOARD_API_MODEL_KEY: {KEYBOARD_ACCESS_ACTION_KEY: {"allowed": True}}
```

**Step 3.** Update `check_keyboard_api_access` in `apps/keyboard_api/auth.py`:
```python
from apps.user_levels.permissions import check_action_allowed
from apps.user_levels.const import KEYBOARD_API_MODEL_KEY, KEYBOARD_ACCESS_ACTION_KEY
from django.core.exceptions import PermissionDenied

def check_keyboard_api_access(user) -> bool:
    try:
        check_action_allowed(user, KEYBOARD_API_MODEL_KEY, KEYBOARD_ACCESS_ACTION_KEY)
        return True
    except PermissionDenied:
        return False
```

**Step 4.** Create a data migration to populate the capability on existing `Level` records.

No URL, middleware, or model changes required.

---

## Response Headers

All responses include:

```
Content-Type: application/json
```

## Error Response Format

All error responses use the same envelope:

```json
{"error": "Human-readable error message."}
```

---

## Django App Structure

```
apps/keyboard_api/
├── __init__.py
├── apps.py            # AppConfig
├── const.py           # Rate limit constants, cache TTLs
├── models.py          # MobileAPIToken (with fcm_token field)
├── admin.py           # Admin registration
├── auth.py            # token_required, firebase_required decorators, rate limiter
├── firebase.py        # Firebase Admin SDK helpers (send_boards_sync_notification)
├── tasks.py           # Celery tasks (notify_boards_changed, notify_board_owner)
├── responses.py       # json_response helper (JsonResponse wrapper)
├── serializers.py     # serialize_full_boards_sync, serialize_boards_list, serialize_board_content
├── views.py           # obtain_token, refresh_token, register_fcm_token, full_boards_sync,
│                      # boards_list, board_content
├── urls.py            # URL patterns under /api/keyboard/
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_mobileapitoken_fcm_token.py
└── README.md          # This file

apps/boards/
├── apps.py            # BoardsConfig — registers signal handlers in ready()
├── models.py          # Board (updated_at), BoardDeleteLog, BoardItem (mosaic_preview)
└── signals.py         # post_save / post_delete: touch Board.updated_at, log deletions,
                       # dispatch FCM tasks; collaborator/library entry hooks
```
