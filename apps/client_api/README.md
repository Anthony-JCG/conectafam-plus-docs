# Fam Fit Client API — Technical Reference

Backend JSON API for the **Fam Fit** native consumer app (client area).
Mount point: `/api/client/`. Mirrors `keyboard_api` patterns (device tokens,
`JsonResponse`, csrf-exempt function views) but authenticates via
`ClientProfile.access_code`, not `users.User` credentials.

Token audiences are isolated: `ClientDeviceToken` is never accepted by
`/api/keyboard/`, and `MobileAPIToken` is never accepted here.

---

## Architecture Overview

```
Advisor (web)                 Client (Fam Fit native app)
─────────────                 ──────────────────────────
users.User                    ClientProfile ↔ Contact
Django session / CSRF         ClientDeviceToken (device_id + hex token)
client_area HTMX pane         Authorization: Token <hex64>
```

Domain models and business rules live in [`apps/client_area`](../client_area/README.md). This app
only exposes the native HTTP contract. Every endpoint reads live from the database; the only cache
is the login rate limit.

---

## Base URL

| Environment | Base |
|-------------|------|
| Local       | `http://localhost:8000/api/client/` |
| Debug       | `https://debug.<host>/api/client/` |
| Prod        | `https://<host>/api/client/` |

---

## Authentication

### Login

`POST /auth/token/`

| Field | Required | Notes |
|-------|----------|-------|
| `access_code` | yes | Advisor-issued code on `ClientProfile` (case-insensitive) |
| `device_id` | yes | Stable UUID from the device |
| `device_name` | no | Human-readable label |

| Status | Description | Body |
|---|---|---|
| `200` | Access active | `{"token": "<64 hex>", "client_profile_id": 1, "access_status": "active", "name": "María Castillo"}` |
| `400` | Invalid JSON, missing `device_id` or `access_code` | `{"error": "..."}` |
| `401` | Unknown code (counts toward the IP rate limit: 10 / 10 minutes) | `{"error": "Invalid access code."}` |
| `403` | Code valid, access not active; ensures one pending `first_access` request | `{"error": "Access is not active.", "access_status": "pending", "client_profile_id": 1}` |
| `429` | Rate limited | `{"error": "Too many failed attempts. Try again later."}` |

### Access lifecycle

`ClientProfile.access_status`, driven by the advisor's web pane and the program lifecycle:

| Event | `access_status` |
|-------|-----------------|
| Login with a valid code while not active | `none` → `pending` + `ClientAccessRequest(first_access)` |
| `POST /continuity/` | `none` → `pending` + `ClientAccessRequest(continuity)` |
| Advisor accepts the request, turns access on, or activates the program (pending requests are accepted) | `active` |
| Advisor turns access off | `deactivated` |
| Program ends: advisor deactivates it, the hourly expiry job ends it after its last day in the client's zone, or the advisor's client-area add-on lapses | `none` ("Sin acceso"); the next login creates a new request |

A renewal starts the same program again with a new period: `/program/` files, products and
`/academy/` (with the lessons already unlocked) are kept; nothing is deleted when a program ends.

Device tokens are not revoked when access changes: authenticated calls keep returning **200** on
the token-only endpoints and **403** `{"error": "Access is not active.", "access_status": "..."}`
on the ones that require active access.

### Authenticated requests

```
Authorization: Token <token>
```

Missing header → **401** `{"error": "Authentication required."}`; unknown token → **401**
`{"error": "Invalid or expired token."}`.

### Client time zone

Send the device's IANA zone on login and on every authenticated request:

```
X-Timezone: America/Guayaquil
```

The server stores it on the profile when it changes (unknown names are ignored, never an error).
The client's calendar follows it everywhere, whoever looks at it (app, advisor web, Celery jobs):
program `day` / `days_remaining` / scheduled `status`, unlocked lessons, the default and the
maximum of `recorded_on`, the end of the program and the 08:00 reminders. Without it the server's
zone (`settings.TIME_ZONE`) is used.

### Refresh / logout

| Method | Path | Response |
|--------|------|----------|
| `POST` | `/auth/token/refresh/` | **200** same body as login; the old token is invalid immediately |
| `POST` | `/auth/logout/` | **200** `{"status": "ok"}`; deletes this device token |

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/token/` | public + rate limit | Login by access code |
| POST | `/auth/token/refresh/` | token | Rotate token |
| POST | `/auth/logout/` | token | Delete device token |
| POST | `/auth/fcm-token/` | token + Firebase | Register device FCM token |
| GET | `/me/` | token | Basic profile + program summary + `profile_complete` |
| GET · PATCH | `/profile/` | token | "Mi perfil": sex, birth date, height, neck, activity level |
| GET | `/home/` | token + active | Greeting, current metrics, weekly deltas, advisor WhatsApp |
| GET | `/measurements/` | token | Measurement history (charts) |
| POST | `/measurements/` | token + active | Save the day's measurement (upsert per date) |
| GET | `/photos/` | token | Progress photo history |
| POST | `/photos/` | token + active | Save the day's photos, multipart front/back/side (upsert per date) |
| GET | `/program/` | token + active | Latest file per slot (nutrition/sport/other) + products |
| GET | `/products/` | token | Products of the active program |
| GET | `/products/<id>/` | token | Product detail (popup) |
| GET | `/academy/` | token + active | Programas formativos with their lessons (per-lesson availability) + `todays_lesson` |
| GET | `/academy/lessons/<id>/` | token + active | Lesson detail if unlocked |
| POST | `/continuity/` | token | Continuity request (order + purchase date) |

Unexpected errors return **500** `{"error": "Internal server error."}` on every endpoint.

---

## Data Structures

### Program

`program` in `/me/`, `/home/` and `/program/` describes the active assignment, or is `null` when
there is none. `/me/` and `/home/` also return a program **scheduled** to start later (a first
program or a renewal) so the app can show "Tu programa inicia {start_date}"; `/program/` and
`/academy/` wait for the start date.

```json
{
  "status": "active",
  "day": 10,
  "start_date": "2026-09-02",
  "duration_days": 90,
  "end_date": "2026-12-01",
  "progress_percent": 11,
  "days_remaining": 80,
  "is_active": true
}
```

| Field | Type | Notes |
|---|---|---|
| `status` | string | `active`, or `scheduled` (starts on `start_date`) |
| `day` | int \| null | 1-based program day; `null` while scheduled. A renewal restarts it at 1 |
| `start_date` | `YYYY-MM-DD` | Set by the advisor; fixed once the program is activated |
| `duration_days` | int | Set by the advisor; fixed once the program is activated |
| `end_date` | `YYYY-MM-DD` | Always `start_date + duration_days` (derived, never stored) |
| `progress_percent` | int | 0–100 |
| `days_remaining` | int \| null | Days until `end_date`; `null` while scheduled |
| `is_active` | bool | Inside the program window and not deactivated (`false` while scheduled) |

Scheduled program in `/me/`:

```json
{
  "access_status": "active",
  "program": { "status": "scheduled", "day": null, "start_date": "2026-10-06", "duration_days": 90, "end_date": "2027-01-04", "progress_percent": 0, "days_remaining": null, "is_active": false },
  "program_finished": false
}
```

### Product

```json
{ "id": 1, "name": "Omega 3", "observations": "1 cápsula al día", "recorded_on": "2026-09-25" }
```

| Field | Type | Notes |
|---|---|---|
| `id` | int | |
| `name` | string | Products text entered by the advisor |
| `observations` | string | `""` when empty |
| `recorded_on` | `YYYY-MM-DD` | Date set by the advisor |

Products are plain text rows with no image or board item. Edits and deletes in the pane show up on
the next request; a row the advisor added but has not named yet is left out of the lists.

### Lesson

| Field | Type | Notes |
|---|---|---|
| `id` | int | |
| `program_id` | int | Id of its programa formativo (`programs[].id` in `/academy/`) |
| `title` | string | Board item title, else the first 80 chars of the text, else the attachment title, else `Lesson <id>` |
| `unlock_day` | int | `0` = always available ("Siempre"); `N >= 1` = available from program day `N` ("Día N") |
| `order` | int | Display order inside its program; sort by it |
| `unlocked` | bool | `unlock_day == 0`, `program_day >= unlock_day`, or a day already reached in a previous period (a renewal restarts `program_day` but keeps what was unlocked) |
| `thumbnail_url` | string \| null | Absolute preview of the content board item, the image the board shows: YouTube `hqdefault` thumbnail, `mosaic_preview` of PDFs / images / pages. `null` when the board has none (uploaded videos, text, PDFs whose preview could not be generated). Sent for locked lessons too |
| `video_url` | string | YouTube URL (`""` otherwise or while locked) |
| `youtube_video_id` | string \| null | 11-char id parsed from `video_url`, for an embedded YouTube player |
| `video_file_url` | string | Absolute file URL of an uploaded video, playable with a native player (`""` otherwise or while locked) |

The video keys come in the `programs[].lessons` list as well, so the app can play a video inline
without opening the detail. Detail payloads (`todays_lesson`, `/academy/lessons/<id>/`) add `text`
and `attachment_url` (strings, `""` when empty). The content of a lesson is always a board item of
the advisor's client-area board (uploads from the pane are stored there first): `text` is the
lesson text, `attachment_url` the file of its attachment item, and the content item fills the key
of its type when it is still empty:

| Item type | Key |
|---|---|
| YouTube | `video_url` |
| Uploaded video | `video_file_url` |
| Text | `text` |
| PDF, image | `attachment_url` |

---

## Endpoint Details

### GET /me/

```json
{
  "client_profile_id": 1,
  "name": "Maria Castillo",
  "access_status": "active",
  "access_code": "ABCD2345",
  "program": { "status": "active", "day": 10, "start_date": "2026-09-02", "duration_days": 90, "end_date": "2026-12-01", "progress_percent": 11, "days_remaining": 80, "is_active": true },
  "program_finished": false,
  "profile_complete": true
}
```

`profile_complete` is `false` while a value of `/profile/` is missing (the app asks for them).
`program_finished` is `true` when access is `active` but no program runs (neither active nor
scheduled). Once a program
ends, access goes back to `none`, so the response has `access_status: "none"`, `program: null` and
`program_finished: false`; the app offers `POST /continuity/`.

### GET /home/

```json
{
  "greeting_name": "Maria Castillo",
  "access_status": "active",
  "program": { "status": "active", "day": 10, "start_date": "2026-09-02", "duration_days": 90, "end_date": "2026-12-01", "progress_percent": 11, "days_remaining": 80, "is_active": true },
  "current": {
    "id": 12,
    "recorded_on": "2026-09-25",
    "weight": 72.0,
    "waist": 82.0,
    "chest": null,
    "hip": null,
    "arm": null,
    "leg": null,
    "body_fat_pct": 20.0,
    "body_fat_pct_source": "user",
    "muscle_mass_kg": 31.0,
    "muscle_mass_pct": 43.1,
    "muscle_mass_source": "user",
    "daily_kcal": 2150,
    "daily_kcal_source": "calc",
    "bioimpedance": {},
    "source": "client",
    "created_at": "2026-09-25T18:00:00+00:00"
  },
  "weekly_deltas": { "weight": -2.0, "waist": -2.0, "chest": null, "hip": null, "arm": null, "leg": null },
  "advisor_whatsapp_url": "https://wa.me/593999111222"
}
```

`current` is the latest measurement (`null` without one); `weekly_deltas` compares the two latest
(`null` with fewer than two). `current` carries the body composition of that row (see
[Body composition](#body-composition)).

### GET · PATCH /profile/

"Mi perfil", asked on first launch (Guardar / Más tarde) and editable later. Token only.

- **GET** → **200** the values, `missing` (the empty ones, in this order: `sex`, `birth_date`,
  `height_cm`, `neck_cm`, `activity_level`), `profile_complete` and `activity_levels` (choices to
  render, Spanish label and description).
- **PATCH** JSON, any subset; `null` clears a value → **200** same body. **400** `{"error": ...}`
  for a value out of range.

| Field | Values |
|---|---|
| `sex` | `male` / `female` (biological sex) |
| `birth_date` | `YYYY-MM-DD`, age 10–120; stored on the advisor's contact (`Contact.date_of_birth`) |
| `height_cm` | 100–250 |
| `neck_cm` | 20–80 |
| `activity_level` | 1–5 (multipliers 1.2 / 1.375 / 1.55 / 1.725 / 1.9) |

```json
{ "sex": "female", "birth_date": "1990-05-02", "height_cm": 165, "neck_cm": 33 }
```

```json
{
  "sex": "female",
  "birth_date": "1990-05-02",
  "height_cm": 165.0,
  "neck_cm": 33.0,
  "activity_level": null,
  "missing": ["activity_level"],
  "profile_complete": false,
  "activity_levels": [
    { "value": 1, "label": "Sedentario", "description": "Poco o ningún ejercicio.", "multiplier": 1.2 },
    { "value": 2, "label": "Ligero", "description": "Ejercicio ligero 1–3 días por semana.", "multiplier": 1.375 },
    { "value": 3, "label": "Moderado", "description": "Ejercicio moderado 3–5 días por semana.", "multiplier": 1.55 },
    { "value": 4, "label": "Activo", "description": "Ejercicio intenso 6–7 días por semana.", "multiplier": 1.725 },
    { "value": 5, "label": "Muy activo", "description": "Trabajo físico o entrenamiento dos veces al día.", "multiplier": 1.9 }
  ]
}
```

### GET · POST /measurements/

**One record per day.** A client has at most one measurement and one photo record per date. The
app saves with the device's **local date** in `recorded_on` (without it, today in the client's
zone, see `X-Timezone`) and preloads that day's record first: a second save the same day
updates it instead of adding a row.

- **GET** → **200** `{"measurements": [Measurement, ...]}`, newest first.
  `?recorded_on=YYYY-MM-DD` returns only that day (`[]` or one row) to preload the form.
- **POST** JSON upsert of `recorded_on`: `weight`, `waist`, `chest`, `hip`, `arm`, `leg`,
  the optional user values `body_fat_pct` (2–75) and `muscle_mass_kg` (10–150; it replaces
  `bioimpedance.muscle_mass_kg`), and `bioimpedance` (free-form extra readings). Only the keys sent change; `null` clears a value; `bioimpedance` is replaced
  whole. `recorded_on` may be at most the client's tomorrow (slack for a stale zone).
  - **201** `{"measurement": {...}, "created": true}` the first save of the day (`source=client`;
    the advisor gets an `ActivityContact` note and a web push).
  - **200** `{"measurement": {...}, "created": false}` when the day already had a record (no new
    notification; `source` keeps who created it).
  - **400** invalid JSON, bad / future `recorded_on`, or a non-numeric value.

Second save of the day (`chest` was saved earlier and stays):

```json
{ "recorded_on": "2026-10-01", "weight": 69.9, "waist": 80 }
```

```json
{ "measurement": { "id": 12, "recorded_on": "2026-10-01", "weight": 69.9, "waist": 80.0, "chest": 95.0, "hip": null, "arm": null, "leg": null, "body_fat_pct": null, "body_fat_pct_source": null, "muscle_mass_kg": null, "muscle_mass_pct": null, "muscle_mass_source": null, "daily_kcal": null, "daily_kcal_source": null, "bioimpedance": {}, "source": "client", "created_at": "2026-10-01T13:00:00+00:00" }, "created": false }
```

#### Body composition

Every measurement row (list, POST response, `/home/` `current`) has `body_fat_pct` +
`body_fat_pct_source`, `muscle_mass_kg` + `muscle_mass_pct` + `muscle_mass_source` and `daily_kcal`
+ `daily_kcal_source`. A source is `user` exactly when the value is stored on the row (entered by
the client, always wins), `calc` (calculated) or `null` with the value when an input is missing (never guessed).
Calculated with `/profile/` and the row (`client_area.services.body`):

| Value | Formula | Inputs |
|---|---|---|
| `body_fat_pct` | U.S. Navy (Hodgdon & Beckett), cm, log10. Male `495 / (1.0324 − 0.19077·log10(waist − neck) + 0.15456·log10(height)) − 450`; female `495 / (1.29579 − 0.35004·log10(waist + hip − neck) + 0.22100·log10(height)) − 450` | row `waist` (+ `hip` for women), profile `neck_cm`, `height_cm`, `sex` |
| `muscle_mass_kg` | Skeletal muscle, Lee et al. 2000 (Am J Clin Nutr) anthropometric model `0.244·weight + 7.8·height_m + 6.6·sex − 0.098·age − 3.3` (sex 1 male / 0 female, race term 0) | row `weight`, age on the row's date, profile `height_cm`, `sex` |
| `muscle_mass_pct` | `muscle_mass_kg / weight × 100` (user or calc kg) | row `weight` |
| `daily_kcal` | Mifflin-St Jeor BMR (male `10W + 6.25H − 5A + 5`, female `… − 161`) × activity multiplier, rounded | row `weight`, age on the row's date, profile `height_cm`, `sex`, `activity_level` |

```json
{ "id": 12, "recorded_on": "2026-10-01", "weight": 80.0, "waist": 90.0, "chest": null, "hip": null, "arm": null, "leg": null, "body_fat_pct": 18.4, "body_fat_pct_source": "calc", "muscle_mass_kg": 33.3, "muscle_mass_pct": 41.6, "muscle_mass_source": "calc", "daily_kcal": 2712, "daily_kcal_source": "calc", "bioimpedance": {}, "source": "client", "created_at": "2026-10-01T13:00:00+00:00" }
```

### GET · POST /photos/

- **GET** → **200** `{"photos": [{"id", "recorded_on", "front_url", "back_url", "side_url", "source", "created_at"}]}`;
  `?recorded_on=YYYY-MM-DD` returns only that day.
- **POST** multipart upsert of `recorded_on` (same rules): at least one of `front` / `back` /
  `side`; the slots sent replace the day's, the others stay. **201** `{"photo": {...}, "created": true}`
  or **200** `{"photo": {...}, "created": false}` with absolute URLs, **400** without images.
  Photos are stored as WebP (max 1280 px wide); a replaced slot deletes its previous file, so
  always use the URLs of the latest response.

Rows the advisor deletes in the web pane are only hidden there; both lists keep returning them.

### GET /program/

```json
{
  "program": { "day": 10, "start_date": "2026-09-02", "duration_days": 90, "end_date": "2026-12-01", "progress_percent": 11, "days_remaining": 80, "is_active": true },
  "files": {
    "nutrition": [{ "id": 1, "slot": "nutrition", "title": "plan", "file_url": "https://.../plan.pdf", "thumbnail_url": "https://.../mosaic_previews/3f9c0a1b2c4d.webp", "assigned_on": "2026-09-25" }],
    "sport": [],
    "other": []
  },
  "products": [{ "id": 1, "name": "Omega 3", "observations": "...", "recorded_on": "2026-09-25" }]
}
```

Every program file is a board item of the advisor's client-area board (uploads are stored there,
in Nutrición / Deporte / Otros): `title` is the item title, `file_url` its file or URL and
`thumbnail_url` the absolute preview the web grid shows (`mosaic_preview` of a PDF or image, YouTube
thumbnail), or `null` when the board has none (e.g. a PDF whose first page could not be rendered).
Without an active program: `program: null`, empty slots and `products: []`.

The advisor's Programa table has dated rows with one cell per slot; the client always follows the
**latest file of each slot**. Each `files.<slot>` list therefore holds at most one file: the newest
non-empty cell of that slot, by row date and then row id (a later row with that cell empty keeps the
previous file). `[]` means no row fills the slot. `assigned_on` is the date of the file's row, which
the advisor's pane sets to the local date whenever a cell is filled; `id` is the cell id.

### GET /products/ · GET /products/<id>/

| Status | Body |
|---|---|
| `200` | `{"products": [Product, ...]}`, newest `recorded_on` first (active program only; `[]` without one) |
| `200` | `{"product": Product}` for `/products/<id>/` (any product of this client) |
| `404` | `{"error": "Product not found."}`: unknown, another client's, or deleted by the advisor |

### GET /academy/

```json
{
  "academy_enabled": true,
  "program_day": 10,
  "todays_lesson": { "id": 3, "program_id": 8, "title": "Hoy", "unlock_day": 10, "order": 1, "unlocked": true, "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg", "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube_video_id": "dQw4w9WgXcQ", "video_file_url": "", "text": "", "attachment_url": "" },
  "programs": [
    {
      "id": 7,
      "name": "Deporte en casa",
      "order": 1,
      "lessons": [
        { "id": 4, "program_id": 7, "title": "Bienvenida", "unlock_day": 0, "order": 1, "unlocked": true, "thumbnail_url": null, "video_url": "", "youtube_video_id": null, "video_file_url": "https://.../clase.mp4" },
        { "id": 1, "program_id": 7, "title": "Dia 1", "unlock_day": 1, "order": 2, "unlocked": true, "thumbnail_url": "https://.../mosaic_previews/ab12.webp", "video_url": "", "youtube_video_id": null, "video_file_url": "" },
        { "id": 2, "program_id": 7, "title": "Dia 20", "unlock_day": 20, "order": 3, "unlocked": false, "thumbnail_url": "https://i.ytimg.com/vi/aBcDeFgHiJk/hqdefault.jpg", "video_url": "", "youtube_video_id": null, "video_file_url": "" }
      ]
    },
    {
      "id": 8,
      "name": "Desarrollo personal",
      "order": 2,
      "lessons": [{ "id": 3, "program_id": 8, "title": "Hoy", "unlock_day": 10, "order": 1, "unlocked": true, "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg", "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube_video_id": "dQw4w9WgXcQ", "video_file_url": "" }]
    }
  ]
}
```

| Field | Notes |
|---|---|
| `academy_enabled` | Advisor's No/Sí toggle; `false` also without an active program |
| `program_day` | 1-based program day, `null` without a start date |
| `todays_lesson` | Detail of the first lesson (programs, then lessons, in order) whose `unlock_day` equals `program_day`, or `null`. `unlock_day: 0` lessons are never `todays_lesson` |
| `programs` | Programas formativos (the Academia folders), sorted by `order`: `id`, `name`, `order` and `lessons` (Lesson list with thumbnail and video keys, without `text` / `attachment_url`, sorted by `order`). Each lesson carries its own `unlock_day`; both kinds may be mixed |

When `academy_enabled` is `false`: `programs: []`, `todays_lesson: null`.

**Contract change (programas formativos).** The top-level `lessons` list was removed: lessons now
come grouped in `programs[].lessons`, and every lesson (list, `todays_lesson` and detail) has
`program_id`. `unlock_day`, `unlocked`, `todays_lesson` and the detail keys are unchanged; the
lesson `title` no longer falls back to a video URL (content always comes from a board item).

### GET /academy/lessons/<id>/

| Status | Body |
|---|---|
| `200` | `{"lesson": Lesson + detail keys}` |
| `403` | `{"error": "Lesson is locked.", "unlock_day": 20, "unlocked": false}` |
| `403` | `{"error": "Academy is not enabled."}` |
| `403` | `{"error": "Access is not active.", "access_status": "..."}` |
| `404` | `{"error": "Lesson not found."}` |

### POST /continuity/

Body: `order_number`, `purchase_date` (`YYYY-MM-DD`). Creates or refreshes a pending
`ClientAccessRequest(kind=continuity)`, moves access from `none` to `pending`, and notifies the
advisor (ActivityContact + web push + inbox). Does **not** require active access.

**201**:

```json
{
  "request_id": 5,
  "kind": "continuity",
  "status": "pending",
  "order_number": "ORD-42",
  "purchase_date": "2026-09-20",
  "access_status": "pending",
  "advisor_whatsapp_url": "https://wa.me/593999111222?text=...",
  "whatsapp_message": "Hola, quiero continuar mi programa Fam Fit. Pedido: ORD-42. Fecha de compra: 2026-09-20."
}
```

**400** for invalid JSON, a missing field or a malformed date.

### POST /auth/fcm-token/

Body: `{"fcm_token": "..."}`. Stores the FCM registration token on `ClientDeviceToken`.
**200** `{"status": "ok"}`, **400** without `fcm_token`, **503** when Firebase Admin is not
initialised. Call after login and on OS token rotation.

---

## FCM Events

| `event` | When |
|-------|------|
| `client_weigh_reminder` | 08:00 client time; program day ∈ {6, 13, 20, 27} ("weigh tomorrow") |
| `client_program_ending` | 08:00 client time; `days_remaining == 4` |

Beat task: `client_api.tasks.send_client_reminders`, hourly; each run pushes to the clients whose
local time (`X-Timezone`) is 08:00, with their program day of that date. The advisor side of
`POST /measurements/` uses web push (`client_new_measurement`), not FCM.

---

## Errors

| Status | Meaning |
|--------|---------|
| 400 | Invalid JSON / missing or invalid fields |
| 401 | Missing/invalid token or access code |
| 403 | Access not active, academy disabled, or lesson locked |
| 404 | Resource not found or owned by another client |
| 429 | Auth rate limit |
| 503 | Firebase not initialised (`/auth/fcm-token/`) |
| 500 | Unexpected server error |

Error bodies are `{"error": "<message>"}`, plus the extra keys listed per endpoint.
