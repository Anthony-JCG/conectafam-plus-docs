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

## Endpoints (rama 1)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/token/` | public + rate limit | Login by access code |
| `POST` | `/auth/token/refresh/` | token | Rotate token |
| `POST` | `/auth/logout/` | token | Delete device token |
| `GET` | `/me/` | token | Basic profile + program summary |

### `GET /me/`

```json
{
  "client_profile_id": 1,
  "name": "María Castillo",
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
```

Later ramas add home/progress, program files, academy, continuity, and FCM.

---

## Errors

| Status | Meaning |
|--------|---------|
| 400 | Invalid JSON / missing fields |
| 401 | Missing/invalid token or access code |
| 403 | Access not active |
| 429 | Auth rate limit |
| 500 | Unexpected server error |
