# Keyboard API — Referencia técnica

API backend que alimenta el **teclado global móvil** — una app compañera del módulo Boards de
Conectafam Plus. El teclado opera como una extensión aislada, capaz de funcionar sin conexión.
Todos los datos se almacenan localmente en el dispositivo; el teclado solo lee de ese almacén local
y nunca hace llamadas directas a la API durante el uso.

---

## Visión general de la arquitectura

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

### Justificación del diseño

Las extensiones de teclado en iOS y Android son procesos aislados (sandbox) con memoria estricta
(~30–50 MB en iOS) y sin acceso garantizado a la red. Llamar a la API directamente desde la
extensión es poco fiable y viola las políticas de seguridad de la plataforma.

La arquitectura elegida separa las responsabilidades de forma limpia:

- **Sincronización inicial** — en el primer login la app principal descarga el snapshot completo de
  tableros y lo escribe en un contenedor compartido (App Group en iOS, almacenamiento compartido en
  Android).
- **Sincronización incremental** — cuando cambia cualquier tablero, carpeta o ítem en la web, se
  disparan Django Signals y el servidor envía una **notificación push silenciosa de Firebase** a
  todos los dispositivos registrados de los usuarios afectados. La app principal la recibe en
  segundo plano, llama a `GET /sync/` y actualiza el almacenamiento local.
- **Extensión de teclado** — lee exclusivamente del almacenamiento local. Sin dependencia de red en
  el momento de uso.

---

## Flujo de sincronización

```
── First login ──────────────────────────────────────────────────────────

1. POST /api/keyboard/auth/token/
   → store token securely (Keychain / Keystore)

2. POST /api/keyboard/auth/fcm-token/
   → register FCM device token

3. GET  /api/keyboard/sync/estimate/
   → show download-size prompt (Apple 4.2.3(ii)) before fetching media

4. GET  /api/keyboard/sync/            (no ?since — full sync)
   → is_full_sync: true
   → store all boards + store synced_at value locally
   → keyboard extension now has complete offline data

── Normal use ───────────────────────────────────────────────────────────

5. [Web] User edits a board (any folder, item, or board metadata)
   → Django signal touches Board.updated_at
   → Celery task sends silent FCM push to affected devices

6. Main app receives FCM push  (data.event == "boards_changed")
   → GET /api/keyboard/sync/?since=<last synced_at>  (delta sync)
   → is_full_sync: false
   → upsert changed boards into local store
   → remove deleted_board_ids from local store
   → update stored synced_at to the new value

── keyboard extension reads only from local storage ─────────────────────
```

---

## URL base

| Entorno | URL base |
|---|---|
| Producción | `https://conectafam-plus.com/api/keyboard/` |
| Desarrollo local (`runserver`) | `http://localhost:8000/api/keyboard/` |
| Desarrollo local (Docker) | `http://localhost:${WEB_PORT}/api/keyboard/` — Nginx hace de front de Gunicorn, que escucha en `:8080` dentro del contenedor. Ver [`docs/docker.es.md`](../../docs/docker.es.md) |

---

## Autenticación

La API usa **autenticación basada en token** (sin cookies de sesión, sin CSRF). Todo endpoint
protegido requiere:

```
Authorization: Token <token>
```

Los tokens son cadenas hexadecimales de 64 caracteres (256 bits de entropía vía
`secrets.token_hex(32)`). Existe un token por par `(user, device_id)` — un mismo usuario puede estar
autenticado en varios dispositivos a la vez. Los tokens son persistentes; usa el endpoint de refresh
para rotación de seguridad.

---

## Endpoints

### 1. Obtener token

**`POST /api/keyboard/auth/token/`**

Autentica con las credenciales de la plataforma y devuelve un token de dispositivo persistente. No
requiere cabecera `Authorization`.

#### Cuerpo de la petición (JSON)

```json
{
  "username": "string",
  "password": "string",
  "device_id": "string",
  "device_name": "string"
}
```

| Campo | Obligatorio | Descripción |
|---|---|---|
| `username` | Sí | Nombre de usuario de Conectafam Plus |
| `password` | Sí | Contraseña de Conectafam Plus |
| `device_id` | Sí | UUID estable generado en la primera instalación; se guarda en Keychain / Keystore |
| `device_name` | No | Etiqueta legible mostrada en admin (p. ej. `"iPhone 15 Pro"`) |

#### Respuestas

| Status | Descripción | Body |
|---|---|---|
| `200 OK` | Token emitido | `{"token": "...", "user_id": 42, "username": "johndoe"}` |
| `400 Bad Request` | JSON malformado o falta `device_id` | `{"error": "..."}` |
| `401 Unauthorized` | Credenciales incorrectas | `{"error": "Invalid credentials."}` |
| `403 Forbidden` | La cuenta no tiene acceso a la Keyboard API | `{"error": "Your account does not have access to this API."}` |
| `429 Too Many Requests` | Límite de tasa por IP superado | `{"error": "Too many failed attempts. Try again later."}` |

**Limitación de tasa:** 10 intentos fallidos por IP en una ventana de 10 minutos (respaldado por
Redis).

---

### 2. Refrescar token

**`POST /api/keyboard/auth/token/refresh/`**

Rota el token actual e invalida el anterior. Úsalo para rotación periódica de seguridad.

#### Cabeceras de la petición

```
Authorization: Token <current_token>
```

No se requiere cuerpo de petición.

#### Respuestas

| Status | Descripción | Body |
|---|---|---|
| `200 OK` | Nuevo token emitido | `{"token": "...", "user_id": 42, "username": "johndoe"}` |
| `401 Unauthorized` | Token ausente o inválido | `{"error": "Invalid or expired token."}` |

---

### 3. Registrar token FCM

**`POST /api/keyboard/auth/fcm-token/`**

Guarda o actualiza el token de registro de Firebase Cloud Messaging de este dispositivo. El servidor
lo usa para entregar notificaciones push silenciosas de sincronización cuando cambian los datos de
los tableros.

Llama a este endpoint:
- Inmediatamente después de un login correcto (`obtain_token`).
- Cada vez que el SO rote el token FCM (el SDK de FCM ofrece un callback `onTokenRefresh` /
  `didReceiveRegistrationToken` para este evento).

#### Cabeceras de la petición

```
Authorization: Token <token>
Content-Type: application/json
```

#### Cuerpo de la petición (JSON)

```json
{"fcm_token": "string"}
```

#### Respuestas

| Status | Descripción | Body |
|---|---|---|
| `200 OK` | Token FCM guardado | `{"status": "ok"}` |
| `400 Bad Request` | `fcm_token` ausente o vacío | `{"error": "fcm_token is required."}` |
| `401 Unauthorized` | Token ausente o inválido | `{"error": "..."}` |
| `503 Service Unavailable` | Firebase no inicializado en el servidor | `{"error": "Push notification service unavailable."}` |

---

### 4. Sincronización de tableros (completa y delta)

**`GET /api/keyboard/sync/`** — sync completa (primer login)
**`GET /api/keyboard/sync/?since=<ISO8601>`** — sync delta (actualizaciones posteriores)

El mismo endpoint cubre ambos modos. La presencia del parámetro `since` selecciona el modo.

**Nunca** llames a este endpoint desde dentro de la propia extensión de teclado — solo el proceso
de la app principal debe hacerlo y después escribir el resultado en App Group / almacenamiento
compartido.

#### Parámetros de query

| Param | Obligatorio | Descripción |
|---|---|---|
| `since` | No | Datetime ISO 8601 con zona horaria — el valor `synced_at` de la respuesta anterior. Omítelo para una sync completa. |

#### Cabeceras de la petición

```
Authorization: Token <token>
```

#### Respuestas

| Status | Descripción | Body |
|---|---|---|
| `200 OK` | Payload de sync | `SyncResponse` (ver Estructuras de datos) |
| `400 Bad Request` | Valor `since` no parseable | `{"error": "Invalid 'since' parameter. ..."}` |
| `401 Unauthorized` | Token ausente o inválido | `{"error": "..."}` |
| `500 Internal Server Error` | Error inesperado | `{"error": "Internal server error."}` |

#### Rendimiento de sync completa (sin `since`)

| Query | Qué obtiene |
|---|---|
| 4 búsquedas de IDs | IDs de tableros propios, de biblioteca, de colaborador y públicos |
| 1 query de boards | Todas las filas Board con owner (`select_related`) |
| 1 query de folders | Todas las filas BoardFolder (bulk) |
| 1 query de items | Todas las filas BoardItem con landing page (bulk, `select_related`) |

#### Rendimiento de sync delta (`?since=`)

| Query | Qué obtiene |
|---|---|
| 4 búsquedas de IDs | Misma resolución de acceso que la sync completa |
| 1 query de IDs cambiados | IDs de Board con `updated_at > since` |
| 1 query de boards | Solo las filas Board cambiadas |
| 1 query de borrados | Entradas de `BoardDeleteLog` con `deleted_at > since` |
| 1 query de folders | Solo carpetas de los tableros cambiados |
| 1 query de items | Solo ítems de los tableros cambiados |

En una edición típica (un tablero cambiado), las queries 5–6 devuelven una sola fila cada una. El
tamaño del payload es proporcional a lo que realmente cambió.

#### Limitación de la sync delta

`deleted_board_ids` solo cubre borrados permanentes de tableros. Los tableros que dejan de ser
accesibles por un cambio de permisos (p. ej. el propietario revoca el acceso público, se elimina un
colaborador) **no** se incluyen. Mitígalo haciendo una sync completa periódicamente (p. ej. una vez
al día o con un pull-to-refresh explícito del usuario) para purgar tableros obsoletos del almacén
local.

---

### 5. Estimación de tamaño de medios offline

**`GET /api/keyboard/sync/estimate/`**

Devuelve solo el tamaño total en bytes y el número de archivos de una caché offline completa de
todos los tableros a los que el usuario tiene acceso. Lo usa la app host Flutter para mostrar un
aviso de tamaño de descarga **antes** de llamar a `GET /sync/` y descargar medios (Apple App Store
guideline 4.2.3(ii)).

**No** devuelve tableros, ítems, URLs ni medios. La forma de `GET /sync/` no cambia.

Llámalo tras el login (y antes de la primera sync completa / descarga de medios). La extensión de
teclado nunca llama a este endpoint.

#### Cabeceras de la petición

```
Authorization: Token <token>
```

Sin parámetros de query.

#### Respuestas

| Status | Descripción | Body |
|---|---|---|
| `200 OK` | Totales de tamaño | `{"bytes": int, "file_count": int}` |
| `401 Unauthorized` | Token ausente o inválido | `{"error": "..."}` |
| `500 Internal Server Error` | Error inesperado | `{"error": "Internal server error."}` |

#### Cuerpo de la respuesta

```json
{
  "bytes": 1684488192,
  "file_count": 1234
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `bytes` | `int` | Suma de cada `cover_image_size` (board) + `file_size` (ítem) + `preview_size` (ítem) distinto de cero que el usuario descargaría en una caché offline completa. Mismas reglas que `/sync/`: `0` significa sin archivo / sin preview / sin portada y se omite. |
| `file_count` | `int` | Cuántos de esos campos de tamaño eran distintos de cero (cada campo no cero cuenta como un archivo). |

Ambos campos son siempre enteros JSON presentes (nunca null, nunca omitidos). Catálogo vacío:

```json
{"bytes": 0, "file_count": 0}
```

La resolución de acceso coincide con `GET /sync/` (propios + biblioteca + colaborador + públicos).
Los tamaños se persisten en `Board.cover_image_size`, `BoardItem.file_size` y `BoardItem.preview_size`
al subir o cambiar medios, así que este endpoint es un `SUM` / `COUNT` SQL — sin HEAD por archivo
ni descarga de medios. El payload es mínimo (Gzip opcional).

---

### 6. Listar tableros (navegación progresiva)

**`GET /api/keyboard/boards/`**

Devuelve una lista ligera de tableros sin carpetas ni ítems. Disponible como alternativa a la sync
completa cuando solo se necesita la lista de tableros.

#### Cabeceras de la petición

```
Authorization: Token <token>
```

#### Respuestas

| Status | Descripción | Body |
|---|---|---|
| `200 OK` | Éxito | `{"boards": [BoardSummary, ...]}` |
| `401 Unauthorized` | Token ausente o inválido | `{"error": "..."}` |
| `500 Internal Server Error` | Error inesperado | `{"error": "Internal server error."}` |

---

### 7. Obtener contenido de un tablero (un nivel)

**`GET /api/keyboard/boards/<board_id>/`**

Devuelve carpetas e ítems de un nivel de carpeta. Omite `folder_id` para la raíz del tablero; pásalo
para entrar en una subcarpeta.

#### Cabeceras de la petición

```
Authorization: Token <token>
```

#### Parámetros de query

| Param | Obligatorio | Descripción |
|---|---|---|
| `folder_id` | No | Carpeta a abrir; omítelo para la raíz del tablero |

#### Respuestas

| Status | Descripción | Body |
|---|---|---|
| `200 OK` | Éxito | `BoardContentResponse` |
| `400 Bad Request` | `folder_id` inválido | `{"error": "Invalid folder_id."}` |
| `401 Unauthorized` | Token ausente o inválido | `{"error": "..."}` |
| `404 Not Found` | Tablero/carpeta no encontrado o sin acceso | `{"error": "Board not found."}` |
| `500 Internal Server Error` | Error inesperado | `{"error": "Internal server error."}` |

---

## Estructuras de datos

### FullBoard (desde `GET /sync/`)

```json
{
  "id": 1,
  "title": "Marketing Resources",
  "description": "Links and files for the marketing team.",
  "cover_image": "https://conectafam-plus.com/media/boards/covers/cover.jpg",
  "cover_image_size": 24576,
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

`folders` contiene **todas** las carpetas del tablero (no solo las de raíz). `items` contiene
**todos** los ítems del tablero en todas las carpetas. Ambas son listas planas; el cliente
reconstruye el árbol con `parent_id` en carpetas y `folder_id` en ítems.

- `folder.parent_id = null` → carpeta de nivel raíz
- `item.folder_id = null` → ítem de nivel raíz (fuera de cualquier carpeta)
- `item.folder_id = 5` → el ítem pertenece a la carpeta con `id: 5`
- `url` → URL web absoluta de la página de detalle del tablero (`/boards/<id>/`)

### BoardSummary (desde `GET /boards/`)

```json
{
  "id": 1,
  "title": "Marketing Resources",
  "description": "Links and files for the marketing team.",
  "cover_image": "https://conectafam-plus.com/media/boards/covers/cover.jpg",
  "cover_image_size": 24576,
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

### BoardContentResponse (desde `GET /boards/<id>/`)

```json
{
  "board": {"...BoardSummary fields..."},
  "folder_id": null,
  "folders": [FolderSummary],
  "items": [ItemObject]
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `board` | `BoardSummary` | Metadatos del tablero (incluye `updated_at`) |
| `folder_id` | `int \| null` | Carpeta abierta actualmente (`null` = raíz del tablero) |
| `folders` | `FolderSummary[]` | Carpetas hijas directas solo en este nivel |
| `items` | `ItemObject[]` | Ítems solo en este nivel |

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

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | Clave primaria de la carpeta |
| `kind` | `"folder"` | Siempre `"folder"` |
| `parent_id` | `int \| null` | ID de la carpeta padre, o `null` para carpetas de nivel raíz |
| `title` | `string` | Nombre visible de la carpeta |
| `order` | `int` | Posición de orden dentro del padre |

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
  "file_size": 1048576,
  "file_mime_type": "audio/mpeg",
  "share_url": "https://conectafam-plus.com/media/boards/files/recording",
  "preview_url": "",
  "preview_size": 0,
  "youtube_video_id": "",
  "landing_page_id": null,
  "order": 1
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | Clave primaria del ítem |
| `kind` | `"item"` | Siempre `"item"` |
| `folder_id` | `int \| null` | Carpeta a la que pertenece; `null` = ítem raíz |
| `item_type` | `string` | Ver tabla de tipos de ítem |
| `title` | `string` | Título crudo tal como se guarda (puede estar vacío) |
| `display_title` | `string` | Título de visualización resuelto — nunca vacío |
| `text_content` | `string` | Texto completo para ítems `text`; vacío en los demás |
| `url` | `string` | URL externa para ítems `link` y `youtube` |
| `file_url` | `string` | URL absoluta del archivo multimedia |
| `file_name` | `string` | Nombre de archivo tal como se guarda en el servidor (p. ej. `"recording.m4a"`). Úsalo como nombre sugerido al descargar o compartir. Vacío si el ítem no tiene archivo. |
| `file_size` | `int` | Tamaño del archivo multimedia en bytes. `0` cuando el ítem no tiene archivo. |
| `file_mime_type` | `string` | Tipo MIME inferido de la extensión del nombre, con fallbacks por tipo para archivos guardados sin extensión (p. ej. `"audio/mpeg"` para `voice`, `"video/mp4"` para `video`). Vacío si el ítem no tiene archivo. |
| `share_url` | `string` | Mejor URL para pegar o compartir este ítem externamente |
| `preview_url` | `string` | URL de miniatura o imagen de previsualización |
| `preview_size` | `int` | Tamaño en bytes de la miniatura `mosaic_preview` generada en el servidor. `0` cuando no existe archivo de preview. |
| `youtube_video_id` | `string` | ID de vídeo de YouTube extraído, o `""` |
| `landing_page_id` | `int \| null` | ID de la landing page vinculada, o `null` |
| `order` | `int` | Posición de orden dentro de su padre |

#### Tipos de ítem

| `item_type` | Descripción | Campos poblados |
|---|---|---|
| `text` | Fragmento de texto plano | `text_content` |
| `image` | Imagen subida | `file_url`, `file_name`, `file_size`, `file_mime_type`, `preview_url`, `preview_size` |
| `link` | Enlace web externo | `url`, `share_url` |
| `video` | Vídeo subido | `file_url`, `file_name`, `file_size`, `file_mime_type` |
| `voice` | Grabación de voz | `file_url`, `file_name`, `file_size`, `file_mime_type` |
| `pdf` | Documento PDF | `file_url`, `file_name`, `file_size`, `file_mime_type`, `preview_url`, `preview_size` |
| `youtube` | Vídeo de YouTube | `url`, `youtube_video_id`, `preview_url` |
| `page` | Landing page | `landing_page_id`, `share_url`, `preview_url`, `preview_size` |

#### Notas sobre `preview_url`

- `image`: miniatura WebP de 480 px pregenerada (`mosaic_preview`). Si no existe, cae a la URL del
  archivo original (ítems subidos antes de introducir la generación de miniaturas).
- `pdf`: miniatura WebP de 480 px de la primera página pregenerada (`mosaic_preview`). Cadena vacía
  si aún no se ha generado.
- `youtube`: miniatura estándar (`https://i.ytimg.com/vi/{video_id}/hqdefault.jpg`)
- `page`: imagen de banner de la landing page, si está definida
- `link`: **no se rellena** — obtén las previsualizaciones de enlace en el cliente para evitar HTTP
  saliente durante la sync
- Resto de tipos: cadena vacía

> Las miniaturas `mosaic_preview` se generan en el servidor (PIL para imágenes, PyMuPDF para PDFs)
> en el momento de la subida. No hace falta redimensionar ni renderizar PDF en el cliente.

#### Campos de tamaño de archivo

Todos los valores de tamaño son enteros en **bytes**:

| Campo | Ámbito | `0` significa |
|---|---|---|
| `cover_image_size` | Board | Sin imagen de portada configurada |
| `file_size` | Ítem | El ítem no tiene archivo multimedia subido |
| `preview_size` | Ítem | No existe miniatura `mosaic_preview` en storage |

Los tamaños se persisten en las filas de board/ítem al subir y `/sync/` los expone sin
transformación. Sin medios el valor es `0`. El cliente puede combinar estos campos con
`GET /sync/estimate/` para determinar los requisitos de descarga y almacenamiento offline
antes de obtener los medios.

### SyncResponse

```json
{
  "boards": [FullBoard],
  "deleted_board_ids": [42, 71],
  "synced_at": "2026-06-24T17:30:00.123456+00:00",
  "is_full_sync": false
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `boards` | `FullBoard[]` | Tableros nuevos/cambiados con todas las carpetas e ítems. En sync completa, contiene todos los tableros accesibles. En sync delta, solo tableros con `updated_at > since`. |
| `deleted_board_ids` | `int[]` | IDs de tableros borrados permanentemente desde `since`. Siempre `[]` en sync completa. El cliente debe eliminarlos del almacenamiento local. |
| `synced_at` | `string` | Timestamp UTC ISO 8601. **Guarda este valor y pásalo como `since` en la siguiente llamada de sync.** |
| `is_full_sync` | `bool` | `true` en sync completa (el cliente sustituye todos los tableros locales). `false` en delta (el cliente hace upsert de `boards` y elimina `deleted_board_ids`). |

#### Reglas de merge en el cliente

- **Sync completa (`is_full_sync: true`)**: Sustituye todo el almacén local de tableros por `boards`.
- **Sync delta (`is_full_sync: false`)**:
  1. Por cada tablero en `boards`: haz upsert en el almacén local (reemplaza si existe, inserta si es nuevo).
  2. Por cada ID en `deleted_board_ids`: elimina el tablero correspondiente del almacenamiento local.
  3. Actualiza el `synced_at` guardado al nuevo valor.

#### Guía de procesamiento en el cliente

La app principal posee todo el I/O de red. La extensión de teclado no debe llamar nunca a la API.

**Estructura del almacén local**

Persiste como mínimo:

| Key | Tipo | Propósito |
|---|---|---|
| `boards` | `FullBoard[]` | Copia offline completa indexada por `id` del tablero |
| `synced_at` | string ISO 8601 | Timestamp de la última sync correcta — pásalo como `?since=` en sync delta |
| `auth_token` | string | Token de API por dispositivo (Keychain / Keystore) |
| `fcm_token` | string | Registrado con `POST /auth/fcm-token/` |

Cada upsert de `FullBoard` sustituye el registro completo del tablero (metadatos + todas las
carpetas + todos los ítems). No intentes parchear campo a campo dentro de un tablero — el servidor
siempre envía el subárbol completo del tablero cuando hay cambios.

**Cuándo hacer sync completa vs delta**

| Disparador | Endpoint | Acción del cliente |
|---|---|---|
| Primer login | `GET /sync/` | Sustituir todo el almacén local; guardar `synced_at` |
| FCM `boards_changed` | `GET /sync/?since=<synced_at>` | Upsert de `boards`; eliminar `deleted_board_ids`; guardar el nuevo `synced_at` |
| App en primer plano tras >24 h inactiva | `GET /sync/` | Sync completa — purga tableros perdidos por cambios de permisos |
| Pull-to-refresh del usuario | `GET /sync/` | Sync completa |
| Login en dispositivo nuevo (mismo usuario) | `GET /sync/` | Sync completa en ese dispositivo |
| Tras guardar un tablero público en la web (otra pestaña/dispositivo) | Esperar FCM o sync completa al pasar a primer plano | Los tableros públicos no se descubren individualmente por push (ver más abajo) |

**Handler FCM (solo proceso de la app principal)**

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

**Algoritmo de upsert (delta)**

Por cada tablero en `response.boards`:

1. Si el `id` del tablero existe en local → borra carpetas/ítems antiguos y reemplázalos con el payload entrante.
2. Si el `id` del tablero es nuevo → inserta el tablero entero.
3. Reconstruye cualquier índice en memoria (árbol de carpetas, lookup de ítems por `id`).

Por cada `id` en `response.deleted_board_ids`:

1. Elimina el tablero `id` del almacén local.
2. Elimina cualquier archivo multimedia en caché ligado exclusivamente a ese tablero (limpieza opcional).

**Visibilidad del tablero tras la sync**

Usa las flags de acceso de cada tablero solo para etiquetas de UI — no afectan a la lógica de merge:

| Flag | Significado |
|---|---|
| `is_owner` | El usuario creó este tablero |
| `is_library` | El usuario lo guardó vía enlace de compartición |
| `is_collaborator` | El usuario fue añadido como colaborador |
| `is_public` | Visible porque `is_public = true` en el servidor |

Un tablero puede tener varias flags a la vez (p. ej. owner + public).

**Campos de previsualización**

- `preview_url` en los ítems lo genera el servidor y es seguro cachearlo en local.
- En ítems `page`, `preview_url` refleja el banner/imagen de perfil de la landing vinculada. Cuando
  el título o las imágenes de la landing cambian en la web, el servidor regenera la miniatura del
  ítem e incluye el tablero actualizado en el siguiente delta.
- En ítems `link`, `preview_url` siempre está vacío — resuelve las previsualizaciones en el cliente
  si hace falta.

**Casos límite por cambio de permisos**

La sync delta no puede detectar tableros que dejaron de ser accesibles (colaborador eliminado,
tablero pasado a privado, entrada quitada de la biblioteca). Esos tableros permanecen en el
almacenamiento local hasta una sync completa. Programa una sync completa al pasar la app a primer
plano tras un periodo prolongado de inactividad para purgar entradas obsoletas.

Los tableros públicos creados por otros usuarios nunca reciben notificación push individual (el
fan-out a todos los usuarios autenticados no escala). Aparecen en la siguiente sync completa.

---

## Reglas de visibilidad de tableros

La API devuelve todos los tableros que el usuario puede ver, aplicando las mismas reglas que la web
de Conectafam Plus:

1. **Owned** — tableros creados por el usuario
2. **Library** — tableros guardados vía `BoardLibraryEntry`
3. **Collaborated** — tableros donde el usuario es `BoardCollaborator`
4. **Public** — tableros con `is_public = True`, visibles para todos los usuarios autenticados

Las flags `is_owner`, `is_library`, `is_collaborator` e `is_public` reflejan todas las categorías
aplicables a cada tablero.

---

## Integración con Firebase

### Configuración en el servidor

El Firebase Admin SDK se inicializa en `apps/core/apps.py` (el hook `CoreConfig.ready()`). Lee las
credenciales de la variable de entorno `FIREBASE_CREDENTIALS_JSON` (una cadena JSON). Si la variable
falta o es inválida, Firebase omite la inicialización en silencio y no se envían notificaciones
push.

### Flujo de notificaciones push

Los cambios en el servidor encolan una tarea Celery que envía un push FCM silencioso por cada cambio
de tablero afectado. Los handlers de señales en `apps/boards/signals.py` solo despachan tareas — la
llamada HTTP a FCM nunca corre en el ciclo de la petición web.

#### Matriz de disparadores de sync

| Evento | Señal / hook | `Board.updated_at` actualizado | Destinatarios FCM |
|---|---|---|---|
| Metadatos del tablero creados/actualizados | `post_save(Board)` | Sí (auto_now al guardar) | Propietario, usuarios de biblioteca, colaboradores |
| Carpeta creada/actualizada/eliminada | `post_save/post_delete(BoardFolder)` | Sí (update SQL) | Propietario, usuarios de biblioteca, colaboradores |
| Ítem creado/actualizado/eliminado | `post_save/post_delete(BoardItem)` | Sí (update SQL) | Propietario, usuarios de biblioteca, colaboradores |
| Subida de archivo del ítem + mosaic preview | `BoardItem.save()` (un solo notify) | Sí | Igual — el segundo save interno se suprime |
| Reordenación del mosaico (bulk) | `apply_mosaic_reorder()` | Sí | Igual |
| Cambio de título/imagen de landing (contexto board) | `LandingPage.save()` → `sync_board_page_item_previews()` | Sí | Igual |
| Guardado del editor de bloques de landing (contexto board) | `landing_blocks._sync_board_page_previews_if_needed()` | Sí | Igual |
| Colaborador añadido | `post_save(BoardCollaborator)` | Sí | Propietario, usuarios de biblioteca, colaboradores (incluye al nuevo colaborador) |
| Tablero guardado en biblioteca | `post_save(BoardLibraryEntry)` | Sí | Propietario, usuarios de biblioteca, colaboradores (incluye los dispositivos del usuario que guarda) |
| Tablero borrado permanentemente | `post_delete(Board)` | N/A | Solo el propietario (ver nota de borrado más abajo) |

**Sin notificación push (requieren sync completa en el cliente):**

- Nuevos tableros públicos de otros usuarios — se descubren en la siguiente sync completa.
- Acceso revocado (colaborador eliminado, tablero pasado a privado, entrada de biblioteca
  eliminada) — el tablero obsoleto se purga en sync completa.
- Dispositivos de biblioteca/colaborador al borrar un tablero — el propietario se notifica al
  momento; los demás se reconcilian en la siguiente sync.

La tarea Celery (`apps/keyboard_api/tasks.py`):

1. Recoge los tokens FCM de todos los dispositivos del propietario del tablero, usuarios de
   biblioteca y colaboradores.
2. Envía un `MulticastMessage` con `data: {"event": "boards_changed"}`.
3. Usa `content_available: true` (iOS) y `priority: high` (Android) para disparar un fetch en
   segundo plano sin alerta visible.
4. Registra los fallos por token pero nunca lanza excepción.

#### Borrado de tableros y consistencia eventual

Cuando se borra un tablero, Django elimina en cascada las filas `BoardLibraryEntry` y
`BoardCollaborator` en la misma transacción. Para cuando se dispara `post_delete`, esas filas ya no
existen, así que la tarea solo puede notificar directamente a los dispositivos del propietario.
Los dispositivos de biblioteca y colaboradores **no se notifican de inmediato**.

Se resuelve de forma natural: la siguiente vez que cualquier otro cambio de tablero dispare un push
de sync para esos usuarios, su respuesta de `GET /sync/` simplemente no incluirá el tablero
borrado, y su almacén local se actualizará. No hace falta manejo especial en el cliente — un
snapshot completo nunca contiene tableros obsoletos.

### Manejo en el cliente

La app principal debe implementar un handler de notificaciones en segundo plano que:

1. Compruebe `data["event"] == "boards_changed"`.
2. Llame a `GET /api/keyboard/sync/` con el token guardado.
3. Escriba la respuesta en el contenedor compartido de App Group.

La extensión de teclado lee de ese contenedor compartido al abrirse; nunca inicia peticiones de red.

### Decorador `firebase_required`

Cualquier vista que dependa de que Firebase esté disponible se decora con `@firebase_required`:

```python
@csrf_exempt
@require_POST
@token_required
@firebase_required
def register_fcm_token(request):
    ...
```

Si Firebase no está inicializado, el decorador devuelve `503 Service Unavailable` antes de ejecutar
el cuerpo de la vista, evitando un `NameError` o un no-op silencioso dentro de la vista.

---

## Seguridad

| Control | Implementación |
|---|---|
| **Seguridad de transporte** | HTTPS terminado y forzado por Nginx en producción. Django no define `SECURE_SSL_REDIRECT` ni HSTS — el TLS es enteramente una preocupación de infraestructura ([`docs/docker.es.md`](../../docs/docker.es.md)) |
| **Autenticación** | Basada en token, 256 bits de entropía (`secrets.token_hex(32)`), un token por dispositivo |
| **Protección contra fuerza bruta** | Limitación de tasa por IP en `/auth/token/` (10 intentos / 10 min, Redis) |
| **Rotación de token** | `POST /auth/token/refresh/` para rotación bajo demanda |
| **CSRF** | No aplica — cabecera `Authorization`, sin cookies |
| **Datos sensibles** | Las credenciales nunca se registran en logs; los mensajes de error no revelan si existe el usuario |
| **Control de acceso** | Puerta `check_keyboard_api_access(user)` en todo endpoint protegido |
| **Cuentas inactivas** | Los tokens de usuarios con `is_active=False` se rechazan en el momento de autenticación |
| **Disponibilidad de Firebase** | `@firebase_required` impide que las vistas se ejecuten cuando el SDK no está inicializado |

---

## Futuro: restricciones de acceso por nivel

El acceso actualmente **no** está restringido por nivel: `check_keyboard_api_access(user)` en
`apps/keyboard_api/auth.py` devuelve `user.is_active`. `KEYBOARD_API_MODEL_KEY = "keyboard_api"` ya
está reservado en `apps/user_levels/const.py`; `KEYBOARD_ACCESS_ACTION_KEY` aún no existe.

**Paso 1.** Añadir `KEYBOARD_ACCESS_ACTION_KEY = "access"` a `apps/user_levels/const.py`.

**Paso 2.** Añadir capabilities a `DEFAULT_LEVELS` en `apps/user_levels/capabilities.py`:
```python
KEYBOARD_API_MODEL_KEY: {KEYBOARD_ACCESS_ACTION_KEY: {"allowed": True}}
```

**Paso 3.** Actualizar `check_keyboard_api_access` en `apps/keyboard_api/auth.py`:
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

**Paso 4.** Crear una migración de datos para poblar la capability en los registros `Level`
existentes.

No se requieren cambios de URL, middleware ni modelos.

---

## Cabeceras de respuesta

Todas las respuestas incluyen:

```
Content-Type: application/json
```

## Formato de respuesta de error

Todas las respuestas de error usan el mismo sobre:

```json
{"error": "Human-readable error message."}
```

---

## Estructura de la app Django

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
├── serializers.py     # serialize_full_boards_sync, serialize_sync_estimate,
│                      # serialize_boards_list, serialize_board_content
├── views.py           # obtain_token, refresh_token, register_fcm_token, full_boards_sync,
│                      # sync_estimate, boards_list, board_content
├── urls.py            # URL patterns under /api/keyboard/
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_mobileapitoken_fcm_token.py
└── README.es.md       # Este archivo

apps/boards/
├── apps.py            # BoardsConfig — registers signal handlers in ready()
├── models.py          # Board (updated_at), BoardDeleteLog, BoardItem (mosaic_preview)
└── signals.py         # post_save / post_delete: touch Board.updated_at, log deletions,
                       # dispatch FCM tasks; collaborator/library entry hooks
```
