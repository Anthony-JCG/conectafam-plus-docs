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

Domain models and business rules live in `apps/client_area`. This app only
exposes the native HTTP contract.

---

## Base URL

| Environment | Base |
|-------------|------|
| Local       | `http://localhost:8000/api/client/` |
| Staging / Prod | `https://<host>/api/client/` |

---

## Authentication

### Login

`POST /auth/token/`

| Field | Required | Notes |
|-------|----------|-------|
| `access_code` | yes | Advisor-issued code on `ClientProfile` |
| `device_id` | yes | Stable UUID from the device |
| `device_name` | no | Human-readable label |

**200** — access active:

```json
{
  "token": "<64 hex chars>",
  "client_profile_id": 1,
  "access_status": "active",
  "name": "María Castillo"
}
```

**403** — code valid but access not active (`pending` / `deactivated` / was `none`).
May create an idempotent `ClientAccessRequest(kind=first_access)`.

**401** — unknown code (counts toward IP rate limit: 10 / 10 minutes).

**429** — rate limited.

### Authenticated requests

```
Authorization: Token <token>
```

### Refresh / logout

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/auth/token/refresh/` | Rotates token; old value invalid immediately |
| `POST` | `/auth/logout/` | Deletes this device token |

---

## Endpoints (rama 1–4)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/token/ | public + rate limit | Login by access code |
| POST | /auth/token/refresh/ | token | Rotate token |
| POST | /auth/logout/ | token | Delete device token |
| GET | /me/ | token | Basic profile + program summary |
| GET | /home/ | token + active | Greeting, current metrics, weekly deltas, advisor WhatsApp |
| GET | /measurements/ | token | Measurement history (charts) |
| POST | /measurements/ | token + active | Create measurement (source=client) |
| GET | /photos/ | token | Progress photo history |
| POST | /photos/ | token + active | Multipart front/back/side (source=client) |
| GET | /program/ | token + active | PDF slots (nutrition/sport/other) + product summary |
| GET | /products/ | token | Nutritional products list |
| GET | /products/<id>/ | token | Product detail (popup) |
| GET | /academy/ | token + active | Lessons with drip unlock + todays_lesson |
| GET | /academy/lessons/<id>/ | token + active | Lesson detail if unlocked |
| POST | /continuity/ | token | Continuity request (order + purchase date) |

### GET /me/

`json
{
  "client_profile_id": 1,
  "name": "Maria Castillo",
  "access_status": "active",
  "access_code": "ABCD2345",
  "program": {
    "day": 10,
    "duration_days": 90,
    "end_date": "2026-12-01",
    "progress_percent": 11,
    "days_remaining": 80,
    "is_active": true
  },
  "program_finished": false
}
`

### GET /home/

`json
{
  "greeting_name": "Maria Castillo",
  "access_status": "active",
  "program": { "day": 10, "duration_days": 90, "end_date": "2026-12-01", "progress_percent": 11, "days_remaining": 80, "is_active": true },
  "current": {
    "id": 12,
    "recorded_on": "2026-09-25",
    "weight": 72.0,
    "waist": 82.0,
    "chest": null,
    "hip": null,
    "arm": null,
    "leg": null,
    "bioimpedance": { "body_fat_pct": 20.0, "muscle_mass_kg": 31.0 },
    "source": "client",
    "created_at": "2026-09-25T18:00:00+00:00"
  },
  "weekly_deltas": { "weight": -2.0, "waist": -2.0, "chest": null, "hip": null, "arm": null, "leg": null },
  "advisor_whatsapp_url": "https://wa.me/593999111222"
}
`

Bioimpedance / daily calories: v1 accepts optional ioimpedance JSON from the app; empty cards are omitted client-side. No server-side scale formulas yet.

### POST /measurements/

JSON body: weight, waist, chest, hip, rm, leg, optional ioimpedance object, optional 
ecorded_on. Persists source=client. **201** { "measurement": {…} }.

### POST /photos/

Multipart: at least one of ront / ack / side, optional 
ecorded_on. Persists source=client. **201** { "photo": {…} } with absolute image URLs.

### GET /program/

```json
{
  "program": { "day": 10, "duration_days": 90, "end_date": "2026-12-01", "progress_percent": 11, "days_remaining": 80, "is_active": true },
  "files": {
    "nutrition": [{ "id": 1, "slot": "nutrition", "title": "plan.pdf", "file_url": "https://...", "assigned_on": "2026-09-25" }],
    "sport": [],
    "other": []
  },
  "products": [{ "id": 1, "name": "Omega 3", "observations": "...", "recorded_on": "2026-09-25", "image_url": "" }]
}
```

### GET /academy/

Drip: `unlocked` when `program_day >= unlock_day`. Mode `all` unlocks every lesson. Locked lesson detail returns **403**.

```json
{
  "academy_enabled": true,
  "unlock_mode": "drip",
  "program_day": 10,
  "todays_lesson": { "id": 3, "title": "Hoy", "unlock_day": 10, "order": 2, "unlocked": true, "video_url": "...", "video_file_url": "", "text": "Hoy", "attachment_url": "" },
  "lessons": [
    { "id": 1, "title": "Dia 1", "unlock_day": 1, "order": 0, "unlocked": true },
    { "id": 2, "title": "Dia 20", "unlock_day": 20, "order": 1, "unlocked": false }
  ],
  "folders": [{ "id": 9, "title": "Videoteca" }]
}
```

### POST /continuity/

Body: `order_number`, `purchase_date` (YYYY-MM-DD). Creates or refreshes pending `ClientAccessRequest(kind=continuity)`, notifies advisor (ActivityContact + web push), visible in advisor inbox. Does **not** require active access (typical after program end).

**201** example:

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

Later ramas add FCM.

---

## Errors

| Status | Meaning |
|--------|---------|
| 400 | Invalid JSON / missing fields |
| 401 | Missing/invalid token or access code |
| 403 | Access not active |
| 429 | Auth rate limit |
| 500 | Unexpected server error |
