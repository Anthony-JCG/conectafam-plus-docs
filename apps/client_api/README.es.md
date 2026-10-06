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
| Termina el programa: lo desactiva el asesor, lo cierra la expiración horaria tras su último día en la zona del cliente o al asesor se le acaba el add-on del área de clientes | `none` ("Sin acceso"); el siguiente login crea una solicitud nueva |

Una renovación vuelve a poner en marcha el mismo programa con un periodo nuevo: los archivos de
`/program/`, los productos y `/academy/` (con las lecciones ya desbloqueadas) se mantienen; al
terminar un programa no se borra nada.

Los tokens de dispositivo no se revocan cuando cambia el acceso: las llamadas autenticadas siguen
dando **200** en los endpoints que solo piden token y **403**
`{"error": "Access is not active.", "access_status": "..."}` en los que exigen acceso activo.

### Peticiones autenticadas

```
Authorization: Token <token>
```

Sin cabecera → **401** `{"error": "Authentication required."}`; token desconocido → **401**
`{"error": "Invalid or expired token."}`.

### Zona horaria del cliente

Manda la zona IANA del dispositivo en el login y en cada petición autenticada:

```
X-Timezone: America/Guayaquil
```

El servidor la guarda en el perfil cuando cambia (los nombres desconocidos se ignoran, nunca dan
error). El calendario del cliente la sigue en todas partes, lo mire quien lo mire (app, web del
asesor, tareas de Celery): `day` / `days_remaining` / `status` programado, lecciones desbloqueadas,
el valor por defecto y el máximo de `recorded_on`, el fin del programa y los avisos de las 08:00.
Sin ella se usa la zona del servidor (`settings.TIME_ZONE`).

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
| GET | `/me/` | token | Perfil básico + resumen del programa + `profile_complete` |
| GET · PATCH | `/profile/` | token | "Mi perfil": sexo, fecha de nacimiento, altura, nivel de actividad |
| GET | `/home/` | token + activo | Saludo, métricas actuales, deltas semanales, WhatsApp del asesor |
| GET | `/measurements/` | token | Historial de medidas (gráficas) |
| POST | `/measurements/` | token + activo | Guarda la medida del día (upsert por fecha) |
| GET | `/photos/` | token | Historial de fotos de evolución |
| POST | `/photos/` | token + activo | Guarda las fotos del día, multipart frente/espalda/lado (upsert por fecha) |
| GET | `/program/` | token + activo | Último archivo de cada hueco (nutrition/sport/other) + productos |
| GET | `/products/` | token | Productos del programa en curso (activo o programado) |
| GET | `/products/<id>/` | token | Detalle de producto (popup) |
| GET | `/academy/` | token + activo | Programas formativos con sus lecciones (cada una con su disponibilidad) + `todays_lesson` |
| GET | `/academy/lessons/<id>/` | token + activo | Detalle de la lección si está abierta |
| POST | `/continuity/` | token | Solicitud de continuidad (pedido + fecha de compra) |

Cualquier error inesperado devuelve **500** `{"error": "Internal server error."}`.

---

## Estructuras de datos

### Program

`program` en `/me/`, `/home/` y `/program/` describe la asignación activa, o es `null` si no hay
ninguna. `/me/` y `/home/` también devuelven un programa **programado** para empezar más adelante
(un primer programa o una renovación), para que la app muestre "Tu programa inicia {start_date}".
`/program/` y `/products/` también lo devuelven con sus archivos y productos (y el resto de endpoints
funciona); solo `/academy/` (Tu día) espera a la fecha de inicio y hasta entonces responde
`academy_enabled: false`.

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

| Campo | Tipo | Notas |
|---|---|---|
| `status` | string | `active`, o `scheduled` (empieza el `start_date`) |
| `day` | int \| null | Día del programa empezando en 1; `null` mientras está programado. Una renovación lo reinicia en 1 |
| `start_date` | `YYYY-MM-DD` | La fija el asesor; no cambia una vez activado el programa |
| `duration_days` | int | La fija el asesor; no cambia una vez activado el programa |
| `end_date` | `YYYY-MM-DD` | Siempre `start_date + duration_days` (se calcula, no se guarda) |
| `progress_percent` | int | De 0 a 100 |
| `days_remaining` | int \| null | Días hasta `end_date`; `null` mientras está programado |
| `is_active` | bool | Dentro de la ventana del programa y sin desactivar (`false` mientras está programado) |

Programa programado en `/me/`:

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

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int | |
| `name` | string | Texto de productos que escribe el asesor |
| `observations` | string | `""` si está vacío |
| `recorded_on` | `YYYY-MM-DD` | Fecha que fija el asesor |

Los productos son filas de texto, sin imagen ni elemento de board. Lo que se edite o borre en el
panel aparece en la siguiente petición; una fila que el asesor añadió y aún no nombró queda fuera de
las listas.

### Lesson

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int | Estable mientras el cliente tenga el elemento (un elemento de plantilla conserva su id) |
| `program_id` | int | Id de su programa formativo (`programs[].id` en `/academy/`) |
| `title` | string | Título del contenido (contenido de academia de la plantilla o elemento de board); si no, los 80 primeros caracteres del texto; si no, el título del adjunto; si no, `Lesson <id>` |
| `unlock_day` | int | `0` = siempre disponible ("Siempre"); `N >= 1` = disponible desde el día `N` del programa ("Día N"). Valor efectivo: el día propio del cliente o, si no tiene, el de la plantilla |
| `order` | int | Posición dentro de su programa, desde 1 (primero los elementos de plantilla, en el orden de la plantilla, y después los propios del asesor); ordenad por él |
| `unlocked` | bool | `unlock_day == 0`, `program_day >= unlock_day`, o un día ya alcanzado en un periodo anterior (una renovación reinicia `program_day` pero mantiene lo desbloqueado) |
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

Las lecciones de un **programa de plantilla** (el asesor asignó una plantilla de Videoteca) leen en
vivo el contenido de academia de la plantilla: `video_url` es su enlace de YouTube, `text` su texto y
`attachment_url` su adjunto; en ellas `video_file_url` siempre es `""`. Lo que se añade a la plantilla
aparece como lecciones nuevas (ids nuevos) en la siguiente petición; un contenido que se quita de la
plantilla, o que se oculta a este cliente, deja de listarse y su detalle responde `404`.

---

## Detalle de endpoints

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

`profile_complete` es `false` mientras falte algún dato de `/profile/` (la app los pide).
`program_finished` es `true` cuando el acceso está `active` pero no hay programa en curso (ni activo
ni programado). Cuando un
programa termina, el acceso vuelve a `none`, así que la respuesta trae `access_status: "none"`,
`program: null` y `program_finished: false`; la app ofrece `POST /continuity/`.

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
    "muscle_mass_kg": 31.0,
    "daily_kcal": 2150,
    "daily_kcal_source": "calc",
    "bmi": 23.5,
    "bmi_category": "normal",
    "bmi_category_label": "Peso normal",
    "bioimpedance": {},
    "source": "client",
    "created_at": "2026-09-25T18:00:00+00:00"
  },
  "weekly_deltas": { "weight": -2.0, "waist": -2.0, "chest": null, "hip": null, "arm": null, "leg": null },
  "advisor_whatsapp_url": "https://wa.me/593999111222"
}
```

`current` es la última medida (`null` si no hay); `weekly_deltas` compara las dos últimas (`null`
si hay menos de dos). `current` trae la composición corporal de esa fila (ver
[Composición corporal](#composición-corporal)).

### GET · PATCH /profile/

"Mi perfil", que se pide en el primer arranque (Guardar / Más tarde) y se puede editar después. Solo
token.

- **GET** → **200** los valores, `missing` (los vacíos, en este orden: `sex`, `birth_date`,
  `height_cm`, `activity_level`; todos los usa la fórmula de kcal), `profile_complete` y `activity_levels` (opciones para
  pintar, con etiqueta y descripción en español).
- **PATCH** JSON, cualquier subconjunto; `null` borra un valor → **200** el mismo cuerpo. **400**
  `{"error": ...}` si un valor está fuera de rango.

| Campo | Valores |
|---|---|
| `sex` | `male` / `female` (sexo biológico) |
| `birth_date` | `YYYY-MM-DD`, edad 10–120; se guarda en el contacto del asesor (`Contact.date_of_birth`) |
| `height_cm` | 100–250 |
| `activity_level` | 1–5 (multiplicadores 1.2 / 1.375 / 1.55 / 1.725 / 1.9) |

```json
{ "sex": "female", "birth_date": "1990-05-02", "height_cm": 165 }
```

```json
{
  "sex": "female",
  "birth_date": "1990-05-02",
  "height_cm": 165.0,
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

**Un registro por día.** Un cliente tiene como mucho una medida y un registro de fotos por fecha.
La app guarda con la **fecha local del dispositivo** en `recorded_on` (si no llega, el hoy en la
zona del cliente, ver `X-Timezone`) y antes precarga el registro de ese día: guardar
otra vez el mismo día lo actualiza en lugar de añadir una fila.

- **GET** → **200** `{"measurements": [Measurement, ...]}`, de la más reciente a la más antigua.
  `?recorded_on=YYYY-MM-DD` devuelve solo ese día (`[]` o una fila) para precargar el formulario.
- **POST** JSON, upsert del `recorded_on`: `weight`, `waist`, `chest`, `hip`, `arm`, `leg`,
  los valores opcionales del usuario `body_fat_pct` (2–75, nunca se calcula) y `muscle_mass_kg` (10–150, nunca se calcula; sustituye a
  `bioimpedance.muscle_mass_kg`), y `bioimpedance` (otras lecturas, formato libre). Solo cambian las claves enviadas; `null` borra un valor; `bioimpedance` se
  reemplaza entero. `recorded_on` puede ser como mucho el mañana del cliente (margen por si la zona
  guardada está desfasada).
  - **201** `{"measurement": {...}, "created": true}` la primera vez del día (`source=client`; el
    asesor recibe una nota en `ActivityContact` y un web push).
  - **200** `{"measurement": {...}, "created": false}` si el día ya tenía registro (sin nueva
    notificación; `source` sigue diciendo quién lo creó).
  - **400** JSON no válido, `recorded_on` mal formado o futuro, o un valor no numérico.

Segundo guardado del día (`chest` ya estaba guardado y se mantiene):

```json
{ "recorded_on": "2026-10-01", "weight": 69.9, "waist": 80 }
```

```json
{ "measurement": { "id": 12, "recorded_on": "2026-10-01", "weight": 69.9, "waist": 80.0, "chest": 95.0, "hip": null, "arm": null, "leg": null, "body_fat_pct": null, "muscle_mass_kg": null, "daily_kcal": null, "daily_kcal_source": null, "bmi": null, "bmi_category": null, "bmi_category_label": null, "bioimpedance": {}, "source": "client", "created_at": "2026-10-01T13:00:00+00:00" }, "created": false }
```

#### Composición corporal

Cada fila de medidas (lista, respuesta del POST, `current` de `/home/`) trae `body_fat_pct`,
`muscle_mass_kg`, `daily_kcal` + `daily_kcal_source` y `bmi` + `bmi_category` +
`bmi_category_label`.

- `body_fat_pct` y `muscle_mass_kg` son solo los valores que introdujo el cliente (si no, `null`);
  nunca se calculan.
- `daily_kcal_source` es `calc`, o `null` junto al valor si falta algún dato (nunca se inventa).
- El `bmi` (IMC) siempre se calcula: no se guarda ni se acepta en el POST.

Se calcula con `/profile/` y la fila (`client_area.services.body`):

| Valor | Fórmula | Datos |
|---|---|---|
| `daily_kcal` | TMB de Mifflin-St Jeor (hombre `10P + 6.25A − 5E + 5`, mujer `… − 161`) × multiplicador de actividad, redondeado | `weight` de la fila, edad en la fecha de la fila, `height_cm`, `sex` y `activity_level` del perfil |
| `bmi` | `peso / altura_m²`, 1 decimal | `weight` de la fila, `height_cm` del perfil |
| `bmi_category` / `bmi_category_label` | Según el `bmi` redondeado: `< 18.5` `underweight` "Bajo peso", `< 25` `normal` "Peso normal", `< 30` `overweight` "Sobrepeso", si no `obese` "Obesidad" | `bmi` |

```json
{ "id": 12, "recorded_on": "2026-10-01", "weight": 80.0, "waist": 90.0, "chest": null, "hip": null, "arm": null, "leg": null, "body_fat_pct": null, "muscle_mass_kg": null, "daily_kcal": 2712, "daily_kcal_source": "calc", "bmi": 24.7, "bmi_category": "normal", "bmi_category_label": "Peso normal", "bioimpedance": {}, "source": "client", "created_at": "2026-10-01T13:00:00+00:00" }
```

### GET · POST /photos/

- **GET** → **200** `{"photos": [{"id", "recorded_on", "front_url", "back_url", "side_url", "source", "created_at"}]}`;
  `?recorded_on=YYYY-MM-DD` devuelve solo ese día.
- **POST** multipart, upsert del `recorded_on` (mismas reglas): al menos una de `front` / `back` /
  `side`; las que llegan sustituyen a las del día y el resto se mantiene. **201**
  `{"photo": {...}, "created": true}` o **200** `{"photo": {...}, "created": false}` con URLs
  absolutas, **400** si no llega ninguna imagen. Las fotos se guardan en WebP (máx. 1280 px de
  ancho); al sustituir un hueco se borra su archivo anterior, así que usa siempre las URLs de la
  última respuesta.

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
se pudo renderizar). Sin programa en curso (activo o programado): `program: null`, huecos vacíos y `products: []`.

La tabla Programa del asesor tiene filas con fecha y una celda por hueco; el cliente siempre sigue el
**último archivo de cada hueco**. Por eso cada lista `files.<slot>` trae como mucho un archivo: la
celda con archivo más reciente de ese hueco, por fecha de fila y después por id de fila (una fila
posterior con esa celda vacía mantiene el archivo anterior). `[]` significa que ninguna fila rellena
el hueco. `assigned_on` es la fecha de la fila del archivo, que el panel del asesor pone a la fecha
local cada vez que se rellena una celda; `id` es el id de la celda.

### GET /products/ · GET /products/<id>/

| Status | Body |
|---|---|
| `200` | `{"products": [Product, ...]}`, primero el `recorded_on` más reciente (el programa en curso, activo o programado; `[]` si no hay) |
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
| `academy_enabled` | Interruptor No/Sí del asesor; también es `false` si no hay programa activo (así que mientras está programado) |
| `program_day` | Día del programa empezando en 1; `null` sin fecha de inicio |
| `todays_lesson` | Detalle de la primera lección (programas y luego lecciones, en orden) cuyo `unlock_day` coincide con `program_day`, o `null`. Las lecciones con `unlock_day: 0` nunca son `todays_lesson` |
| `programs` | Programas formativos (las carpetas de Academia) ordenados por `order`: `id`, `name`, `order` y `lessons` (lista de Lesson con miniatura y claves de vídeo, sin `text` / `attachment_url`, ordenada por `order`). Cada lección lleva su `unlock_day` y se pueden mezclar los dos tipos |

Con `academy_enabled` a `false`: `programs: []` y `todays_lesson: null`.

**Cambio de contrato (programas formativos).** Desaparece la lista `lessons` de primer nivel: las
lecciones llegan agrupadas en `programs[].lessons`, y todas (lista, `todays_lesson` y detalle) llevan
`program_id`. `unlock_day`, `unlocked`, `todays_lesson` y las claves de detalle no cambian; el
`title` de la lección ya no usa la URL del vídeo como alternativa (el contenido siempre viene de un
elemento del board).

**Cambio de contrato (plantillas de academia).** No se añade ni se quita ninguna clave. `order` pasa
a ser la posición de la lección en su programa, desde 1 (antes era un valor guardado que podía tener
huecos); ordenar por él sigue funcionando. `unlock_day` siempre es el día efectivo de la lección para
este cliente.

### GET /academy/lessons/<id>/

| Status | Body |
|---|---|
| `200` | `{"lesson": Lesson + claves de detalle}` |
| `403` | `{"error": "Lesson is locked.", "unlock_day": 20, "unlocked": false}` |
| `403` | `{"error": "Academy is not enabled."}` |
| `403` | `{"error": "Access is not active.", "access_status": "..."}` |
| `404` | `{"error": "Lesson not found."}`: no existe, es de otro cliente, el asesor la ocultó o ya no está en su plantilla |

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
| `client_weigh_reminder` | 08:00 hora del cliente; día del programa ∈ {6, 13, 20, 27} ("pésate mañana") |
| `client_program_ending` | 08:00 hora del cliente; `days_remaining == 4` |

Tarea beat: `client_api.tasks.send_client_reminders`, cada hora; cada pasada avisa a los clientes
cuya hora local (`X-Timezone`) son las 08:00, con su día del programa de esa fecha. Del lado del asesor,
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
