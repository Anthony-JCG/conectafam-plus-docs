# Fam Fit Client API — Referencia técnica

API JSON para la app nativa del consumidor **Fam Fit** (área de clientes).
Montaje: `/api/client/`. Sigue los patrones de `keyboard_api` (token por
dispositivo, `JsonResponse`, vistas function-based con `csrf_exempt`), pero
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

Los modelos y las reglas de negocio viven en [`apps/client_area`](../client_area/README.es.md).
Esta app solo expone el contrato HTTP nativo. Todos los endpoints leen en directo de la base de
datos; la única caché es el rate limit del login.

---

## URL base

| Entorno | Base |
|---------|------|
| Local   | `http://localhost:8000/api/client/` |
| Debug   | `https://debug.<host>/api/client/` |
| Prod    | `https://<host>/api/client/` |

---

## Autenticación

### Login

`POST /auth/token/`

| Campo | Obligatorio | Notas |
|-------|-------------|-------|
| `access_code` | sí | Código que emite el asesor en `ClientProfile` (da igual mayúsculas o minúsculas) |
| `device_id` | sí | UUID estable del dispositivo |
| `device_name` | no | Etiqueta legible |

| Status | Descripción | Body |
|---|---|---|
| `200` | Acceso activo | `{"token": "<64 hex>", "client_profile_id": 1, "access_status": "active", "name": "María Castillo"}` |
| `400` | JSON inválido, falta `device_id` o `access_code` | `{"error": "..."}` |
| `401` | Código desconocido (cuenta para el rate limit por IP: 10 / 10 minutos) | `{"error": "Invalid access code."}` |
| `403` | Código válido pero sin acceso activo; asegura una única solicitud `first_access` pendiente | `{"error": "Access is not active.", "access_status": "pending", "client_profile_id": 1}` |
| `429` | Rate limit | `{"error": "Too many failed attempts. Try again later."}` |

### Ciclo del acceso

`ClientProfile.access_status` cambia desde el panel web del asesor y con el ciclo del programa:

| Evento | `access_status` |
|--------|-----------------|
| Login con un código válido sin acceso activo | `none` → `pending` + `ClientAccessRequest(first_access)` |
| `POST /continuity/` | `none` → `pending` + `ClientAccessRequest(continuity)` |
| El asesor acepta la solicitud, activa el acceso o activa el programa (se aceptan las solicitudes pendientes) | `active` |
| El asesor desactiva el acceso | `deactivated` |
| Termina el programa: lo desactiva el asesor, lo cierra la expiración diaria o al asesor se le acaba el add-on del área de clientes | `none` ("Sin acceso"); el siguiente login crea una solicitud nueva |

Los tokens de dispositivo no se revocan cuando cambia el acceso: las llamadas autenticadas siguen
dando **200** en los endpoints que solo piden token y **403**
`{"error": "Access is not active.", "access_status": "..."}` en los que exigen acceso activo.

### Peticiones autenticadas

```
Authorization: Token <token>
```

Sin cabecera → **401** `{"error": "Authentication required."}`; token desconocido → **401**
`{"error": "Invalid or expired token."}`.

### Refresh / logout

| Método | Path | Respuesta |
|--------|------|-----------|
| `POST` | `/auth/token/refresh/` | **200** con el mismo body que el login; el token anterior deja de valer al momento |
| `POST` | `/auth/logout/` | **200** `{"status": "ok"}`; borra el token de este dispositivo |

---

## Endpoints

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/auth/token/` | público + rate limit | Login por código de acceso |
| POST | `/auth/token/refresh/` | token | Rotar el token |
| POST | `/auth/logout/` | token | Borrar el token del dispositivo |
| POST | `/auth/fcm-token/` | token + Firebase | Registrar el token FCM del dispositivo |
| GET | `/me/` | token | Perfil básico + resumen del programa |
| GET | `/home/` | token + activo | Saludo, métricas actuales, deltas semanales, WhatsApp del asesor |
| GET | `/measurements/` | token | Historial de medidas (gráficas) |
| POST | `/measurements/` | token + activo | Alta de medida (`source=client`) |
| GET | `/photos/` | token | Historial de fotos de evolución |
| POST | `/photos/` | token + activo | Multipart frente/espalda/lado (`source=client`) |
| GET | `/program/` | token + activo | Último archivo de cada hueco (nutrition/sport/other) + productos |
| GET | `/products/` | token | Productos del programa activo |
| GET | `/products/<id>/` | token | Detalle de producto (popup) |
| GET | `/academy/` | token + activo | Programas formativos con sus lecciones (cada una con su disponibilidad) + `todays_lesson` |
| GET | `/academy/lessons/<id>/` | token + activo | Detalle de la lección si está abierta |
| POST | `/continuity/` | token | Solicitud de continuidad (pedido + fecha de compra) |

Cualquier error inesperado devuelve **500** `{"error": "Internal server error."}`.

---

## Estructuras de datos

### Program

`program` en `/me/`, `/home/` y `/program/` describe la asignación activa, o es `null` si no hay
ninguna.

```json
{
  "day": 10,
  "start_date": "2026-09-02",
  "duration_days": 90,
  "end_date": "2026-12-01",
  "progress_percent": 11,
  "days_remaining": 80,
  "is_active": true
}
```

| Campo | Tipo | Notas |
|---|---|---|
| `day` | int | Día del programa empezando en 1 (`1` antes de la fecha de inicio) |
| `start_date` | `YYYY-MM-DD` | La fija el asesor; no cambia una vez activado el programa |
| `duration_days` | int | La fija el asesor; no cambia una vez activado el programa |
| `end_date` | `YYYY-MM-DD` | Siempre `start_date + duration_days` (se calcula, no se guarda) |
| `progress_percent` | int | De 0 a 100 |
| `days_remaining` | int | Días hasta `end_date` |
| `is_active` | bool | Dentro de la ventana del programa y sin desactivar |

### Product

```json
{ "id": 1, "name": "Omega 3", "observations": "1 cápsula al día", "recorded_on": "2026-09-25" }
```

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int | |
| `name` | string | Texto de productos que escribe el asesor |
| `observations` | string | `""` si está vacío |
| `recorded_on` | `YYYY-MM-DD` | Fecha que fija el asesor |

Los productos son filas de texto, sin imagen ni elemento de board. Lo que se edite o borre en el
panel aparece en la siguiente petición.

### Lesson

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int | |
| `program_id` | int | Id de su programa formativo (`programs[].id` en `/academy/`) |
| `title` | string | Título del elemento de board; si no, los 80 primeros caracteres del texto; si no, el título del adjunto; si no, `Lesson <id>` |
| `unlock_day` | int | `0` = siempre disponible ("Siempre"); `N >= 1` = disponible desde el día `N` del programa ("Día N") |
| `order` | int | Orden dentro de su programa; ordenad por él |
| `unlocked` | bool | `unlock_day == 0`, o `program_day >= unlock_day` |
| `thumbnail_url` | string \| null | Vista previa absoluta del elemento de contenido, la imagen que muestra el board: miniatura `hqdefault` de YouTube, `mosaic_preview` de PDFs / imágenes / páginas. `null` si el board no tiene (vídeos subidos, texto, PDFs cuya vista previa no se pudo generar). También llega en lecciones bloqueadas |
| `video_url` | string | URL de YouTube (`""` si no lo es o si está bloqueada) |
| `youtube_video_id` | string \| null | Id de 11 caracteres sacado de `video_url`, para un reproductor de YouTube embebido |
| `video_file_url` | string | URL absoluta del vídeo subido, reproducible con un reproductor nativo (`""` si no lo es o si está bloqueada) |

Las claves de vídeo también llegan en la lista `programs[].lessons`, así que la app puede reproducir
un vídeo en la propia lista sin abrir el detalle. Los detalles (`todays_lesson`,
`/academy/lessons/<id>/`) añaden `text` y `attachment_url` (cadenas, `""` si están vacías). El contenido de una lección siempre es un
elemento del board del área de clientes del asesor (lo que se sube desde el panel se guarda antes
ahí): `text` es el texto de la lección, `attachment_url` el archivo de su adjunto, y el elemento de
contenido rellena la clave de su tipo si sigue vacía:

| Tipo de elemento | Clave |
|---|---|
| YouTube | `video_url` |
| Vídeo subido | `video_file_url` |
| Texto | `text` |
| PDF, imagen | `attachment_url` |

---

## Detalle de endpoints

### GET /me/

```json
{
  "client_profile_id": 1,
  "name": "Maria Castillo",
  "access_status": "active",
  "access_code": "ABCD2345",
  "program": { "day": 10, "start_date": "2026-09-02", "duration_days": 90, "end_date": "2026-12-01", "progress_percent": 11, "days_remaining": 80, "is_active": true },
  "program_finished": false
}
```

`program_finished` es `true` cuando el acceso está `active` pero no hay programa activo. Cuando un
programa termina, el acceso vuelve a `none`, así que la respuesta trae `access_status: "none"`,
`program: null` y `program_finished: false`; la app ofrece `POST /continuity/`.

### GET /home/

```json
{
  "greeting_name": "Maria Castillo",
  "access_status": "active",
  "program": { "day": 10, "start_date": "2026-09-02", "duration_days": 90, "end_date": "2026-12-01", "progress_percent": 11, "days_remaining": 80, "is_active": true },
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
```

`current` es la última medida (`null` si no hay); `weekly_deltas` compara las dos últimas (`null`
si hay menos de dos). La app puede mandar un objeto `bioimpedance` opcional; las tarjetas vacías se
ocultan en el cliente y el servidor no aplica fórmulas de báscula.

### GET · POST /measurements/

- **GET** → **200** `{"measurements": [Measurement, ...]}`, de la más reciente a la más antigua.
- **POST** JSON: `weight`, `waist`, `chest`, `hip`, `arm`, `leg`, `bioimpedance` opcional y
  `recorded_on` opcional (por defecto, hoy). Se guarda con `source=client`; el asesor recibe una
  nota en `ActivityContact` y un web push. **201** `{"measurement": {...}}`, **400** si no valida.

### GET · POST /photos/

- **GET** → **200** `{"photos": [{"id", "recorded_on", "front_url", "back_url", "side_url", "source", "created_at"}]}`.
- **POST** multipart: al menos una de `front` / `back` / `side` y `recorded_on` opcional. Se guarda
  con `source=client`. **201** `{"photo": {...}}` con URLs absolutas, **400** si no llega ninguna imagen.

Las filas que el asesor borra en el panel web solo se ocultan allí; las dos listas las siguen
devolviendo.

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

Cada archivo de programa es un elemento del board del área de clientes del asesor (lo subido se
guarda ahí, en Nutrición / Deporte / Otros): `title` es el título del elemento, `file_url` su archivo
o URL y `thumbnail_url` la vista previa absoluta que muestra la tabla web (`mosaic_preview` de un PDF
o imagen, miniatura de YouTube), o `null` si el board no tiene (p. ej. un PDF cuya primera página no
se pudo renderizar). Sin programa activo: `program: null`, huecos vacíos y `products: []`.

La tabla Programa del asesor tiene filas con fecha y una celda por hueco; el cliente siempre sigue el
**último archivo de cada hueco**. Por eso cada lista `files.<slot>` trae como mucho un archivo: la
celda con archivo más reciente de ese hueco, por fecha de fila y después por id de fila (una fila
posterior con esa celda vacía mantiene el archivo anterior). `[]` significa que ninguna fila rellena
el hueco. `assigned_on` es la fecha de la fila del archivo, que el panel del asesor pone a la fecha
local cada vez que se rellena una celda; `id` es el id de la celda.

### GET /products/ · GET /products/<id>/

| Status | Body |
|---|---|
| `200` | `{"products": [Product, ...]}`, primero el `recorded_on` más reciente (solo el programa activo; `[]` si no hay) |
| `200` | `{"product": Product}` en `/products/<id>/` (cualquier producto de este cliente) |
| `404` | `{"error": "Product not found."}`: no existe, es de otro cliente o el asesor lo borró |

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

| Campo | Notas |
|---|---|
| `academy_enabled` | Interruptor No/Sí del asesor; también es `false` si no hay programa activo |
| `program_day` | Día del programa empezando en 1; `null` sin fecha de inicio |
| `todays_lesson` | Detalle de la primera lección (programas y luego lecciones, en orden) cuyo `unlock_day` coincide con `program_day`, o `null`. Las lecciones con `unlock_day: 0` nunca son `todays_lesson` |
| `programs` | Programas formativos (las carpetas de Academia) ordenados por `order`: `id`, `name`, `order` y `lessons` (lista de Lesson con miniatura y claves de vídeo, sin `text` / `attachment_url`, ordenada por `order`). Cada lección lleva su `unlock_day` y se pueden mezclar los dos tipos |

Con `academy_enabled` a `false`: `programs: []` y `todays_lesson: null`.

**Cambio de contrato (programas formativos).** Desaparece la lista `lessons` de primer nivel: las
lecciones llegan agrupadas en `programs[].lessons`, y todas (lista, `todays_lesson` y detalle) llevan
`program_id`. `unlock_day`, `unlocked`, `todays_lesson` y las claves de detalle no cambian; el
`title` de la lección ya no usa la URL del vídeo como alternativa (el contenido siempre viene de un
elemento del board).

### GET /academy/lessons/<id>/

| Status | Body |
|---|---|
| `200` | `{"lesson": Lesson + claves de detalle}` |
| `403` | `{"error": "Lesson is locked.", "unlock_day": 20, "unlocked": false}` |
| `403` | `{"error": "Academy is not enabled."}` |
| `403` | `{"error": "Access is not active.", "access_status": "..."}` |
| `404` | `{"error": "Lesson not found."}` |

### POST /continuity/

Body: `order_number`, `purchase_date` (`YYYY-MM-DD`). Crea o actualiza una
`ClientAccessRequest(kind=continuity)` pendiente, pasa el acceso de `none` a `pending` y avisa al
asesor (ActivityContact + web push + bandeja). **No** exige acceso activo.

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

**400** con JSON inválido, un campo que falta o una fecha mal formada.

### POST /auth/fcm-token/

Body: `{"fcm_token": "..."}`. Guarda el token FCM en `ClientDeviceToken`. **200**
`{"status": "ok"}`, **400** sin `fcm_token`, **503** si Firebase Admin no está inicializado.
Llamarlo tras el login y cada vez que el sistema rote el token.

---

## Eventos FCM

| `event` | Cuándo |
|-------|--------|
| `client_weigh_reminder` | Beat diario; día del programa ∈ {6, 13, 20, 27} ("pésate mañana") |
| `client_program_ending` | Beat diario; `days_remaining == 4` |

Tarea beat: `client_api.tasks.send_client_reminders` (08:00). Del lado del asesor,
`POST /measurements/` usa web push (`client_new_measurement`), no FCM.

---

## Errores

| Status | Significado |
|--------|-------------|
| 400 | JSON inválido / campos que faltan o no son válidos |
| 401 | Token o código de acceso inválido o ausente |
| 403 | Acceso no activo, academia desactivada o lección bloqueada |
| 404 | Recurso inexistente o de otro cliente |
| 429 | Rate limit del login |
| 503 | Firebase sin inicializar (`/auth/fcm-token/`) |
| 500 | Error interno |

Los errores devuelven `{"error": "<mensaje>"}`, más las claves extra que se indican en cada endpoint.
