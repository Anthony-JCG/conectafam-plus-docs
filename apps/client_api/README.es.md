# Fam Fit Client API — Referencia técnica

API JSON para la app nativa del consumidor **Fam Fit** (área de clientes).
Montaje: `/api/client/`. Sigue los patrones de `keyboard_api` (token por
dispositivo, `JsonResponse`, vistas function-based con `csrf_exempt`) pero
autentica con `ClientProfile.access_code`, no con credenciales de `users.User`.

Las audiencias de token están aisladas: `ClientDeviceToken` no se acepta en
`/api/keyboard/`, y `MobileAPIToken` no se acepta aquí.

---

## Visión general

```
Asesor (web)                  Cliente (app nativa Fam Fit)
─────────────                 ──────────────────────────
users.User                    ClientProfile ↔ Contact
sesión Django / CSRF          ClientDeviceToken (device_id + token hex)
panel HTMX client_area        Authorization: Token <hex64>
```

Los modelos y reglas de negocio viven en `apps/client_area`. Esta app solo
expone el contrato HTTP nativo.

---

## URL base

| Entorno | Base |
|---------|------|
| Local   | `http://localhost:8000/api/client/` |
| Staging / Prod | `https://<host>/api/client/` |

---

## Autenticación

### Login

`POST /auth/token/`

| Campo | Obligatorio | Notas |
|-------|-------------|-------|
| `access_code` | sí | Código emitido por el asesor en `ClientProfile` |
| `device_id` | sí | UUID estable del dispositivo |
| `device_name` | no | Etiqueta legible |

**200** — acceso activo:

```json
{
  "token": "<64 hex chars>",
  "client_profile_id": 1,
  "access_status": "active",
  "name": "María Castillo"
}
```

**403** — código válido pero acceso no activo (`pending` / `deactivated` / era `none`).
Puede crear un `ClientAccessRequest(kind=first_access)` idempotente.

**401** — código desconocido (cuenta para el rate limit por IP: 10 / 10 minutos).

**429** — rate limit.

### Peticiones autenticadas

```
Authorization: Token <token>
```

### Refresh / logout

| Método | Path | Notas |
|--------|------|-------|
| `POST` | `/auth/token/refresh/` | Rota el token; el valor anterior queda inválido |
| `POST` | `/auth/logout/` | Borra el token de este dispositivo |

---

## Endpoints (rama 1–2)

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| POST | /auth/token/ | público + rate limit | Login por código de acceso |
| POST | /auth/token/refresh/ | token | Rotar token |
| POST | /auth/logout/ | token | Borrar token del dispositivo |
| GET | /me/ | token | Perfil básico + resumen de programa |
| GET | /home/ | token + activo | Saludo, métricas actuales, deltas semanales, WhatsApp asesor |
| GET | /measurements/ | token | Historial de medidas (gráficas) |
| POST | /measurements/ | token + activo | Alta de medida (source=client) |
| GET | /photos/ | token | Historial de fotos de evolución |
| POST | /photos/ | token + activo | Multipart frente/espalda/lado (source=client) |

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

Bioimpedancia / calorías diarias: v1 acepta ioimpedance JSON opcional desde la app; las cards vacías se omiten en el cliente. Sin fórmulas de báscula en servidor todavía.

### POST /measurements/

Body JSON: weight, waist, chest, hip, rm, leg, ioimpedance opcional, 
ecorded_on opcional. Persiste source=client. **201** { "measurement": {…} }.

### POST /photos/

Multipart: al menos una de ront / ack / side, 
ecorded_on opcional. Persiste source=client. **201** { "photo": {…} } con URLs absolutas.

Ramas posteriores añaden archivos de programa, academia drip, continuidad y FCM.

---

## Errores

| Status | Significado |
|--------|-------------|
| 400 | JSON inválido / campos faltantes |
| 401 | Token o código inválido |
| 403 | Acceso no activo |
| 429 | Rate limit de auth |
| 500 | Error interno |
