# client_area

## Descripción

**Área de clientes** del asesor: programas de nutrición y deporte, códigos de acceso, medidas, fotos
de evolución, productos nutricionales y academia de cada cliente. El consumidor es un
`ClientProfile` ligado a un `communication.Contact`, no un `users.User` del árbol de patrocinio. La
app nativa Fam Fit lee estos datos a través de [`apps/client_api`](../client_api/README.es.md).

Relación con las apps núcleo:

- **`user_levels`** — `CLIENT_AREA_MODEL_KEY` + `ACCESS_ACTION_KEY`. Leader y Leader Pro tienen
  acceso; Basic y Pro no. `user_has_client_area` también acepta el add-on `client_area` comprado
  (`pricing.UserAddon`).
- **`communication`** — `ClientProfile.contact` es OneToOne a `Contact`. El inicio y el fin del
  programa dejan notas en `ActivityContact`. El panel vive en la pestaña **Área de cliente** del
  modal de contacto.
- **`boards`** — los archivos de programa y las lecciones de academia apuntan a un `BoardItem` del
  board del área de clientes del asesor; lo que se sube a mano se guarda antes ahí (ver
  [Board del catálogo](#board-del-catálogo) y [Almacenamiento en el board](#almacenamiento-en-el-board)).
- **`pricing`** — vende el add-on; cuando termina, se pausan los programas del asesor (ver
  [Fin del add-on](#fin-del-add-on-programas-en-pausa)).
- **`users.User`** — el asesor es dueño de `AcademyPlan`. El cliente nunca es este usuario.

## Modelos y datos

| Modelo | Relaciones y campos |
|---|---|
| `ClientProfile` | OneToOne → `communication.Contact`. `access_code` único y `access_status` (`none` / `pending` / `active` / `deactivated`). |
| `ClientProgramAssignment` | FK → `ClientProfile`. `start_date`, `duration_days`, `deactivated_at`, `academy_enabled`. La fecha de fin se calcula (`start_date + duration_days`) y no se guarda. |
| `ClientProgramEntry` | Fila de la tabla Programa: FK → asignación (`program_entries`); `assigned_on` (por defecto `timezone.localdate`). Ordenadas de más nueva a más antigua (`-assigned_on`, `-pk`). |
| `ClientProgramFile` | Una celda: FK → fila (`files`); hueco `nutrition` / `sport` / `other`, único por fila; FK → `BoardItem` (el archivo; lo que se sube se convierte en elemento del board). |
| `ClientProduct` | FK → asignación; `recorded_on`, `products`, `observations`. Solo texto, sin elemento de board. |
| `TrainingProgram` | Programa formativo: FK → asignación (`training_programs`); FK opcional → `AcademyPlan` (`source_plan`); `name`, `order`. Una carpeta de Academia. |
| `ClientLesson` | FK → `TrainingProgram` (`lessons`); un elemento de academia: `board_item` (el contenido: vídeo subido, YouTube o cualquier elemento elegido), `text`, `attachment_item` (elemento PDF / imagen del board), `unlock_day`, `order`; FK opcional → `AcademyPlanItem` (`source_item`). |
| `AcademyPlan` | FK → `users.User` (asesor). Plantilla de un programa formativo: su nombre y sus `AcademyPlanItem`. |
| `AcademyPlanItem` | FK → `AcademyPlan`; `board_item`, `text`, `attachment_item`, `unlock_day`, `order`, igual que `ClientLesson`. |
| `ClientMeasurement` | FK → perfil; medidas y `bioimpedance`; `source=client\|advisor`; `hidden_by_advisor`. |
| `ClientProgressPhoto` | FK → perfil; frente, espalda y lado; `source`; `hidden_by_advisor`. |
| `ClientAccessRequest` | FK → perfil; `kind` primer acceso o continuidad; `order_number` / `purchase_date` opcionales. |

Todo salvo `AcademyPlan` / `AcademyPlanItem` cuelga de `ClientProfile` con `CASCADE`: al borrar el
contacto se borra su área de cliente completa (ver el README de `communication`). Los FK a
`BoardItem` son `SET_NULL`: si se borra el elemento del board, la fila se queda sin él. La excepción
es `ClientProgramFile.board_item` (`CASCADE`): una celda siempre tiene archivo, así que borrar el
elemento vacía la celda.

### Ciclo del programa

| Estado | Condición | Acceso del cliente |
|---|---|---|
| Borrador | `start_date` es `null` | No cambia |
| Activo | `start_date <= hoy <= start_date + duration_days` y `deactivated_at` vacío | `active` (se concede al activar) |
| Terminado | `deactivated_at` relleno (asesor, expiración diaria o fin del add-on) | `none` ("Sin acceso") |

- **Activar** (`activate_program`) guarda la fecha de inicio y la duración, acepta las solicitudes
  de acceso pendientes (`access_actions.grant_access_for_program`) o, si no hay, activa el perfil, y
  deja una nota en `ActivityContact`.
- **Fechas bloqueadas.** En cuanto el programa tiene fecha de inicio, ni esa fecha ni
  `duration_days` cambian: `ProgramPeriodForm(assignment=...)` pinta los dos campos desactivados (se
  ignora lo que llegue en el POST) y `activate_program` lanza `ValueError` si el programa ya está
  activo. Solo **Desactivar** lo termina.
- **Desactivar / expirar.** `deactivate_program` y la tarea diaria `expire_due_programs` rellenan
  `deactivated_at` y llaman a `clear_access_on_program_end` (`access_status=none`); el siguiente
  login en Fam Fit crea una nueva solicitud `first_access`.
- Las herramientas siempre editan la **asignación de trabajo** (`get_or_create_working_assignment`):
  la última sin desactivar o, si no hay, un borrador nuevo. Una asignación terminada conserva su
  contenido, pero el siguiente programa arranca desde un borrador nuevo.

### Fechas locales

Todas las fechas por defecto del área de cliente (medidas, fotos, productos, filas del programa,
la fecha de inicio propuesta) y todos los cálculos de fechas (día del programa, progreso, días
restantes, expiración, recordatorios) usan `timezone.localdate()`, nunca `date.today()`. Con
`USE_TZ = True` es la fecha en la zona horaria activa: `users.middle.TimezoneFromSessionMiddleware`
activa la zona del navegador guardada en la sesión (`session["django_timezone"]`, que envía
`core.views`); en las tareas de Celery y en peticiones sin ella se usa `TIME_ZONE` (`Europe/Madrid`).

### Tabla Programa

- Cada `ClientProgramEntry` es una fila (fecha + una celda por columna); el cliente siempre recibe
  el **último archivo de cada columna**: la celda con archivo más reciente por fecha de fila y,
  después, por id de fila. Es lo que devuelve el endpoint `/program/` de Fam Fit (ver el README de
  `client_api`).
- **Nuevo programa** (`add_program_entry`) añade una fila vacía con la fecha de hoy.
- `set_program_file(entry, slot, ...)` rellena o sustituye una celda con un archivo subido (se
  guarda en la carpeta del board de su columna, ver [Almacenamiento en el board](#almacenamiento-en-el-board))
  o con un elemento elegido del board, y pone la fecha de la fila a hoy.
- Quitar una celda o borrar una fila solo borra las filas del programa; los elementos siguen en el
  board.

### Academia: programas formativos

La Academia es un conjunto de **programas formativos** (`TrainingProgram`) que se muestran como
carpetas; al abrir uno se ven y se gestionan sus elementos (`ClientLesson`). Los programas se crean,
se renombran y se borran (al borrar uno se van sus elementos, pero sus elementos del board se
quedan). El interruptor No/Sí `academy_enabled` sigue en la asignación y vale para todos.

Los programas son de la **asignación del cliente**, no del asesor:

- La disponibilidad cuenta desde el día de programa de cada cliente, igual que ya hacían las
  lecciones.
- Se reutilizan con **Plantillas**: un `AcademyPlan` guarda un programa formativo. "Guardar como
  plantilla" (`save_program_as_plan`) guarda el programa abierto con su nombre y, si el asesor ya
  tiene una plantilla con ese nombre, reemplaza sus elementos; "Añadir desde plantilla"
  (`add_program_from_plan`) añade un programa nuevo con una copia de los elementos de la plantilla
  (`source_plan` / `source_item`) y activa la academia. "Copiar de otro cliente"
  (`copy_academy_from_client`) sustituye todos los programas del cliente por una copia de los del
  otro.
- El contenido reutilizable es el propio board: `Videoteca / <nombre del programa>` guarda lo que se
  sube para cualquier cliente cuyo programa se llame así.

### Disponibilidad de la academia

Cada `ClientLesson` tiene su propia disponibilidad en `unlock_day` (`UNLOCK_DAY_ALWAYS = 0`):

| `unlock_day` | Etiqueta en el panel | Se abre |
|---|---|---|
| `0` | Siempre | Siempre, mientras la academia esté activada |
| `N >= 1` | Día N | Cuando `program_day >= N` |

`todays_lesson` es la primera lección (programas y lecciones en orden) cuyo `unlock_day` coincide con
el día actual del programa; las de "Siempre" nunca lo son. La asignación solo guarda el interruptor No/Sí `academy_enabled`; no hay un
modo para toda la academia. Las plantillas y la copia desde otro cliente conservan el `unlock_day` de
cada elemento.

### Servicios

| Módulo | Responsabilidad |
|---|---|
| `services/access.py` | Asignación de códigos de acceso únicos |
| `services/access_actions.py` | Aceptar solicitudes, activar/desactivar el acceso, darlo al iniciar el programa, quitarlo al terminar, textos de WhatsApp de continuidad |
| `services/entitlement.py` | `user_has_client_area(user)`: capability **o** `user_has_addon(user, CLIENT_AREA_ADDON_CODE)` |
| `services/profiles.py` | `get_or_create_client_profile` |
| `services/programs.py` | Asignación de trabajo, `activate_program` / `deactivate_program`, fecha de fin, día del programa, progreso, estado en la tarjeta de contacto y filtro del listado |
| `services/content.py` | Medidas, fotos, `add_program_entry` / `set_program_file`, `add_product(profile, data)`, `hide_by_advisor` |
| `services/academy.py` | `set_academy_enabled`, `create_training_program`, `add_lessons(program, ...)`, `set_lesson_unlock_day`, `save_program_as_plan`, `add_program_from_plan`, `copy_academy_from_client`, `lesson_is_unlocked`, `todays_lesson` |
| `services/catalog.py` | Boards del área de clientes del asesor y búsqueda en el catálogo |
| `services/pane.py` | Contexto del panel, `build_catalog_context`, URLs de WhatsApp |
| `services/inbox.py` | `pending_access_requests_for_advisor` (de la más reciente a la más antigua, con contacto, URL de WhatsApp y antigüedad) para el bloque del home; `HOME_ACCESS_REQUESTS_LIMIT = 3` |
| `services/expiry.py` | Expiración diaria y `pause_programs_without_entitlement` |

## Board del catálogo

El asesor trabaja con **un solo** board, "Área de clientes" (`CLIENT_AREA_OWN_BOARD_TITLE`): su board
privado del área de clientes, que en sus vistas incorpora en solo lectura el catálogo de sistema de
FAM TEAM. Almacenamiento, permisos y carpetas sombra están en el README de `apps/boards` ("Boards del
área de clientes").

| Parte | Dueño | Tipos permitidos | Qué puede hacer el asesor |
|---|---|---|---|
| Catálogo de sistema (Nutrición, Deporte, Videoteca, Otros) | `USER_ROOT` | PDF, imagen; Videoteca también vídeo subido y YouTube | Verlo y elegir elementos; añadir los suyos y subcarpetas dentro de sus carpetas (carpetas sombra) |
| Contenido propio | Asesor | Carpetas, texto, imagen, PDF, vídeo subido, YouTube | CRUD completo dentro de las carpetas del catálogo; nada en la raíz del board |

- `services/pane.build_catalog_context` devuelve `catalog_board` (el board propio).
  `.client-area-tools` lleva su id y la URL de `board_mosaic_data`; el selector de
  `client_area_tools.js` abre ese mosaico combinado, con botón de volver dentro de las carpetas.
  Las fichas de solo lectura se pueden elegir, y lo marcado se mantiene al cambiar de carpeta y al
  buscar.
- `search_client_area_catalog` filtra el índice Redis de boards a esos dos boards y pinta los
  resultados con `textContent`.
- `CatalogItemFormMixin` limita sus `catalog_fields` a
  `get_client_area_catalog_boards_queryset(asesor)`, así que no entra ningún elemento de otro board.
- El widget del campo es `widgets.CatalogPickerInput(multiple=...)`: un botón "Añadir desde board"
  y los ids ocultos que escribe `client_area_tools.js`, por nombre de campo (caben varios selectores
  en un formulario).

| Herramienta | Selector |
|---|---|
| Celda del programa (`ProgramCellForm.board_item`, "Desde board" en el menú de la celda; abre la carpeta de la columna y guarda al elegir) | Un elemento |
| Contenido de academia (`ClientLessonForm.board_items`) | Varios elementos, uno por elemento de academia |
| Adjunto de academia (`ClientLessonForm.attachment_item`) | Un PDF o una imagen |
| Productos nutricionales | Ninguno |

### Almacenamiento en el board

Lo que se sube desde el panel (sin elegirlo del board) se guarda primero como elemento del board, y
el archivo de programa o la lección apunta a él: el elemento del board es la fuente de verdad.
`boards.services.client_area_uploads` decide la carpeta: para un asesor, su carpeta sombra de la
carpeta raíz del catálogo (`ensure_shadow_folder`); para `USER_ROOT`, la propia carpeta del catálogo.

| Subida | Carpeta del board |
|---|---|
| Programa, columna Alimentación (`nutrition`) | Nutrición |
| Programa, columna Deporte (`sport`) | Deporte |
| Programa, columna Otros (`other`) | Otros |
| Academia: vídeo, enlace de YouTube, adjunto | Videoteca / `<nombre del programa>` (la subcarpeta se crea con la primera subida) |

`const.PROGRAM_SLOT_FOLDERS` relaciona cada hueco con su carpeta. La subcarpeta de Videoteca se busca
por nombre en cada subida: renombrar un programa no renombra la carpeta (puede compartirla con
programas de otros clientes que se llamen igual); lo que se suba después va al nombre nuevo.

## Fin del add-on: programas en pausa

Cuando un asesor pierde el área de clientes (termina la suscripción del add-on `client_area`, o
baja de Leader sin tener el add-on), `services/expiry.pause_programs_without_entitlement(asesor)`
ejecuta `deactivate_program` en cada asignación iniciada y sin desactivar: se rellena
`deactivated_at`, el cliente vuelve a "Sin acceso" y queda una nota en `ActivityContact`. "En pausa"
es el estado terminado de arriba; productos, archivos y academia siguen en la asignación.

Disparadores (`signals.py`, encolados tras el commit como `tasks.pause_lapsed_client_programs_task`):

| Señal | Condición |
|---|---|
| `post_save` de `pricing.UserAddon` | `is_active=False` para `client_area` (lo escribe `sync_addon_subscription` con `customer.subscription.deleted` / `.updated`) |
| `post_save` de `user_levels.UserLevelProfile` | Cambio de nivel |

El servicio comprueba primero `user_has_client_area`, así que una subida de nivel que ya incluye
la herramienta no pausa nada. Borrar el contenido tras un periodo de gracia queda fuera (llegará
con el flujo global de bajada de nivel).

## Vistas e integración frontend

**Esta app usa HTMX.** `#pane-cliente`, en el modal de contacto, carga `load_client_area_pane`. Los
usuarios Basic/Pro sin el add-on ven `RestrictedAccessAlert` `client_area_addon`, cuyo botón hace
POST a `pricing.create_addon_checkout` con `client_area`.

Prefijo de URL: **`/client-area/`**

| Endpoint | Nombre | Respuesta |
|---|---|---|
| `load-pane/` | `load_client_area_pane` | Parcial de herramientas (`client-area-tools.html`) |
| `forms/<kind>/` | `client_area_tool_form` | Parcial del formulario para el modal compartido (`views.TOOL_FORMS`) |
| `access/accept/` · `activate/` · `deactivate/` | `client_area_accept_access`, `client_area_activate_access`, `client_area_deactivate_access` | Parcial de herramientas |
| `measurements/add/` · `photos/add/` | `client_area_add_measurement`, `client_area_add_photo` | Parcial de la tabla, o el formulario con errores |
| `measurements/hide/` · `photos/hide/` | `client_area_hide_measurement`, `client_area_hide_photo` | Parcial de la tabla |
| `program/entries/add/` | `client_area_add_program_entry` | Parcial de la tabla del programa (fila nueva) |
| `program/entries/<id>/<slot>/` | `client_area_set_program_file` | `ProgramCellForm` (`file` o `board_item`): parcial de la tabla del programa; toast 422 si no es válido, 404 si el hueco no existe |
| `program/files/<id>/delete/` · `program/entries/<id>/delete/` | `client_area_delete_program_file`, `client_area_delete_program_entry` | Parcial de la tabla del programa |
| `products/add/` | `client_area_add_product` | Parcial de la tabla, o el formulario con errores |
| `products/<id>/edit/` | `client_area_edit_product` | GET: formulario relleno; POST: parcial de la tabla, o el formulario con errores |
| `products/<id>/delete/` | `client_area_delete_product` | Parcial de la tabla |
| `academy/` (GET) | `client_area_academy` | Sección de academia con las carpetas de programas |
| `academy/toggle/` | `client_area_toggle_academy` | Sección de academia (el programa enviado en `program_id` sigue abierto) |
| `academy/programs/add/` | `client_area_add_training_program` | Sección de academia con el programa nuevo abierto; toast 422 si el nombre no es válido |
| `academy/programs/<id>/` (GET) | `client_area_training_program` | Sección de academia con el programa abierto |
| `academy/programs/<id>/rename/` · `delete/` | `client_area_rename_training_program`, `client_area_delete_training_program` | Sección de academia (abierto / carpetas) |
| `academy/programs/<id>/save-template/` | `client_area_save_training_program_template` | Sección de academia, programa abierto |
| `academy/programs/<id>/lessons/add/` | `client_area_add_lesson` | GET: formulario para el modal; POST: tabla de lecciones, o el formulario con errores |
| `academy/lessons/<id>/availability/` | `client_area_set_lesson_availability` | Tabla de lecciones; toast 422 si el dato no es válido |
| `academy/lessons/<id>/delete/` | `client_area_delete_lesson` | Tabla de lecciones |
| `academy/plans/reuse/` · `copy/` | `client_area_reuse_academy_plan`, `client_area_copy_academy` | Sección de academia (el programa nuevo abierto / carpetas) |
| `program/activate/` · `program/deactivate/` | `client_area_activate_program`, `client_area_deactivate_program` | Parcial de herramientas; si el periodo no es válido se vuelve a pintar `#caProgressSection` |
| `access-requests/` | `client_area_access_requests` | Parcial con la lista completa para el modal "Ver todas" del home |
| `access-requests/accept/` | `client_area_accept_access_home` | Bloque del home (swap principal) + lista del modal (OOB); `showToast` |
| `catalog/search/` | `client_area_catalog_search` | Resultados de búsqueda en JSON |

### Modal de formulario compartido

- Las filas de evolución, fotos, productos y academia se añaden con un botón
  **Añadir** que abre `#clientAreaFormModal` (`components/modals/client-area-modals.html`, incluido
  en `contacts.html` fuera de `#contactModal`, junto al selector del catálogo).
- `data-ca-open-form` lo abre con `Modal.show()` y no con `data-bs-toggle`, para que
  `#contactModal` no se cierre. El parcial del formulario (`client-area-tool-form.html`) rellena el
  cuerpo y fija el título con `hx-swap-oob`.
- Si se guarda bien, la vista solo reemplaza el parcial de la tabla y envía `showToast` +
  `clientAreaFormSaved` (cierra el modal). Con errores, el formulario se vuelve a pintar dentro del
  modal con un **200** (`HX-Retarget`).
- Los modales de alta son de una columna (`ToolForm.field_class = "col-12"`); solo Evolución
  (medidas) mantiene dos (`col-12 col-sm-6`). `cotton/tool_add_button` acepta un `url` opcional
  para formularios de un objeto anidado (los elementos de academia de un programa).
- **Secciones del formulario.** Los campos llevan los attrs de sección del repo (`data_section` /
  `data_section_label`, como en `components/form-model.html`). `client-area-tool-form.html` pinta
  el título de la sección cuando cambia, y `cotton/form_field` oculta la etiqueta del campo dentro de
  una sección (la etiqueta es el título).

### Secciones del panel

- **Acceso** — código de acceso con copiar, aceptar solicitud, activar/desactivar el acceso, enlace
  de WhatsApp y badges de App Store / Play Store (provisionales).
- **Evolución / Fotos** — con scroll horizontal. Borrar una fila (la haya creado el cliente o el
  asesor) solo marca `hidden_by_advisor`: desaparece del panel, pero la API de Fam Fit la sigue
  devolviendo.
- **Productos nutricionales** — `ClientProductForm` (fecha, productos, observaciones; sin selector
  del catálogo). Al pulsar una fila se abre el mismo modal ya relleno (`data-ca-open-form` +
  `hx-get`); la celda de borrar es `data-ca-row-action`, el clic de la fila no la tiene en cuenta, y
  lleva un botón `btn-outline-danger` con `hx-confirm`. Borrar elimina la fila. La API lee los
  productos en directo, sin caché.
- **Programa** — `client-area-program-table.html` (`#caProgramTable`, se sustituye con `outerHTML`):
  Fecha, Alimentación, Deporte, Otros y un botón para borrar la fila (`hx-confirm`). Las filas
  salen de `services.pane.build_program_rows` (un `ProgramCell` por columna).
  - Una celda con archivo (`client-area-program-cell.html`) muestra la vista previa del elemento
    del board (`BoardItem.get_preview_url(allow_network=False)`: `mosaic_preview`, la imagen o la
    miniatura de YouTube) o un icono de PDF, con enlace al archivo; debajo, el nombre recortado con
    puntos suspensivos y `components/tooltip-view-more.html` con el nombre completo.
  - Una celda vacía muestra un botón **+** con borde discontinuo. Los dos abren un desplegable
    (`client-area-program-cell-menu.html`): **Subir desde PC** (input de archivo oculto que se envía
    en `change`), **Desde board** (el selector del catálogo se abre en la carpeta de la columna con
    `data-ca-picker-folder`; se puede volver a la raíz) y, si hay archivo, **Quitar**.
  - Cada celda es un formulario: el selector escribe su input oculto (`data-ca-picker-inputs`) y,
    con `data-ca-picker-submit`, `client_area_tools.js` lo envía en el momento.
  - **Nuevo programa**, debajo de la tabla, añade una fila vacía. Los archivos de programa ya no
    usan modal.
- **Academia** — interruptor No/Sí que se guarda al cambiarlo. Cerrada: una carpeta por programa
  formativo (nombre y número de contenidos), un campo "Nuevo programa formativo" y el desplegable
  **Plantillas** ("Añadir desde plantilla" y "Copiar de otro cliente", con `hx-confirm`). Abierta:
  botón de volver, renombrar en línea, borrar (`hx-confirm`), la tabla de elementos, **Añadir
  contenido** y **Guardar como plantilla**. **Añadir contenido** abre `ClientLessonForm`, de una
  columna y por secciones:

  | Sección | Campos |
  |---|---|
  | Disponibilidad | `widgets.AvailabilityWidget`: casilla "Siempre" con el campo "Día" a su derecha (se envían como `unlock_day_always` / `unlock_day`). Marcar Siempre desactiva el día (`client_area_tools.js`); `AvailabilityField` exige un día ≥ 1 salvo con Siempre |
  | Contenido | `widgets.SegmentedRadioSelect` `content_source`: Subir vídeo (`video_file`) / YouTube (`youtube_url`, validado con `extract_youtube_video_id`) / Desde board (`board_items`, varios) |
  | Texto | `text` |
  | Adjuntar archivo (PDF, imagen) | `attachment_source`: Subir archivo (`attachment_file`) / Desde board (`attachment_item`, PDF o imagen) |

  Los campos con `data-ca-when="<origen>=<valor>"` solo se ven con esa opción marcada; `clean()`
  descarta los de las opciones no marcadas y exige algún contenido. `add_lessons` crea un elemento
  por cada contenido (la subida, el YouTube o cada elemento elegido), todos con el texto y el
  adjunto; si solo hay texto o adjunto, uno solo. Cada fila tiene el mismo widget de disponibilidad,
  que se guarda al cambiarlo (al marcar Siempre o al escribir un día), y un botón de borrar con
  `hx-confirm`.
- **Progreso** — `ProgramPeriodForm` (fecha de inicio y duración; la fecha de fin la calcula
  `client_area_tools.js` al momento y nunca se envía). En borrador: **Activar**. Activo: solo
  **Desactivar**; la fecha de inicio y la duración son de solo lectura.
### Bloque de solicitudes del home

`components/card_client_access_requests.html` (`#client-access-requests-section`, lo incluye
`main/home.html` cuando el usuario tiene el área de clientes) muestra las tres últimas
`ClientAccessRequest` pendientes con el componente cotton `<c-access-request-row>`: avatar, nombre
del contacto, qué pide (acceso, o continuar el programa con el número de pedido), hace cuánto
("Hace 2 horas"), un botón de WhatsApp y **Admitir**.

- **Ver todas** abre `#accessRequestsModal` (`components/modals/modal-access-requests.html`,
  extiende `base-modal.html`). Su cuerpo carga `client_area_access_requests` por HTMX cada vez que
  salta `show.bs.modal`, así que la lista siempre está al día; ya no hay una página aparte.
- **Admitir**, desde el bloque o desde el modal, hace POST a `client_area_accept_access_home`, que
  acepta la solicitud (`accept_access_request`) y devuelve el bloque (se reemplaza con `outerHTML`)
  junto con la lista del modal en `hx-swap-oob`, más un `showToast`. Si falla, toast con 422.
- Las dos vistas exigen `user_has_client_area` y solo ven solicitudes de los contactos del propio
  asesor.

## Migraciones

| Migración | Cambio |
|---|---|
| `0005_lesson_unlock_day_always` | `unlock_day` pasa a valer `0` por defecto en `ClientLesson` y `AcademyPlanItem`; las lecciones de asignaciones con `academy_unlock_mode="all"` quedan con `unlock_day=0` (modelos históricos) |
| `0006_remove_academy_unlock_mode_and_folders` | Elimina `ClientProgramAssignment.academy_unlock_mode` y el modelo `ClientProgramFolder` |
| `0007_remove_clientproduct_board_item` | Elimina `ClientProduct.board_item` |
| `0008_remove_clientprogramfile_file` | Elimina `ClientProgramFile.file`: lo que se sube es un elemento del board |
| `0009_trainingprogram` | Crea `TrainingProgram`; añade `ClientLesson.program` (opcional por ahora) y `attachment_item` en `ClientLesson` / `AcademyPlanItem` |
| `0010_default_training_programs` | Datos (modelos históricos): cada asignación con lecciones recibe un "Programa formativo" (renombrable, con el `source_plan` de la asignación) que las agrupa |
| `0011_lesson_board_content_only` | `ClientLesson.program` pasa a ser obligatorio; elimina `ClientLesson.assignment`, `video_url`, `video_file`, `attachment`, los mismos campos de contenido de `AcademyPlanItem` y `ClientProgramAssignment.source_plan` |
| `0012_clientprogramentry` | Crea `ClientProgramEntry`; añade `ClientProgramFile.entry` (nullable) |
| `0013_program_files_to_entries` | Datos (modelos históricos): borra los archivos sin elemento del board; agrupa el resto en una fila por (asignación, fecha), y una columna repetida abre otra fila |
| `0014_program_file_cell` | Elimina `ClientProgramFile.assignment` / `assigned_on`; `entry` y `board_item` (`CASCADE`) pasan a ser obligatorios; único (`entry`, `slot`) |

Los `AcademyPlanItem` guardados desde asignaciones en modo "all" conservan el día que tenían. El
contenido propio de las lecciones en los campos que borra `0011` (URL de vídeo, vídeo, adjunto) no se
convierte en elementos del board.

## Configuración y dependencias

Dependencias: `communication`, `boards`, `users`, `user_levels`, `pricing`. El add-on, sus precios por
nivel y el checkout de Stripe viven en `pricing` (`Addon` con código `client_area`, sembrado por la
migración `0003` de `pricing`). Los archivos van por el backend de almacenamiento global.

| Servicio | Uso |
|---|---|
| Celery beat | `client_area.tasks.expire_client_programs_task` cada día a las 05:15 |
| Celery | `client_area.tasks.pause_lapsed_client_programs_task` (fin del add-on) |
| Redis | La búsqueda del catálogo reutiliza el índice de búsqueda de boards |

No tiene integración propia con Sentry.
