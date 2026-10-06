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
- **`users.User`** — el asesor (dueño del contacto y de sus propias plantillas de academia). El
  cliente nunca es este usuario.

## Modelos y datos

| Modelo | Relaciones y campos |
|---|---|
| `ClientProfile` | OneToOne → `communication.Contact`. `access_code` único, `access_status` (`none` / `pending` / `active` / `deactivated`) y `time_zone` (zona IANA del dispositivo, ver [Fechas locales](#fechas-locales)). "Mi perfil" de Fam Fit: `sex` (`male` / `female`), `height_cm`, `activity_level` (1–5); la fecha de nacimiento es `contact.date_of_birth`. Solo API, no sale en el panel web. |
| `ClientProgramAssignment` | FK → `ClientProfile`. `start_date`, `duration_days`, `deactivated_at`, `academy_enabled`, `unlocked_through_day` (día del programa alcanzado en periodos anteriores). La fecha de fin se calcula (`start_date + duration_days`) y no se guarda. Se reutiliza en cada renovación. |
| `ClientProgramEntry` | Fila de la tabla Programa: FK → asignación (`program_entries`); `assigned_on` (por defecto `timezone.localdate`). Ordenadas de más nueva a más antigua (`-assigned_on`, `-pk`). |
| `ClientProgramFile` | Una celda: FK → fila (`files`); hueco `nutrition` / `sport` / `other`, único por fila; FK → `BoardItem` (el archivo; lo que se sube se convierte en elemento del board). |
| `ClientProduct` | FK → asignación; `recorded_on`, `products`, `observations`. Solo texto, sin elemento de board. |
| `TrainingProgram` | Programa formativo: FK → asignación (`training_programs`); FK opcional → `boards.BoardFolder` (`template_folder`, `SET_NULL`: la plantilla de Videoteca que lee); `name`, `order`. Una carpeta de Academia. Una plantilla está como mucho una vez en la academia de un cliente (`training_program_assignment_template`). |
| `ClientLesson` | FK → `TrainingProgram` (`lessons`); un elemento de academia, ordenado por `order`, `pk`. **Elemento propio**: `board_item` (contenido de YouTube), `text`, `attachment_item` (elemento PDF / imagen del board), `unlock_day`. **Elemento de plantilla**: FK → `BoardItem` (`template_item`, `CASCADE`) cuyo contenido lee; solo guarda lo que cambia para el cliente, `unlock_day` (`null` = el de la plantilla) y `hidden_by_advisor`. Una fila por programa y elemento de plantilla (`client_lesson_program_template_item`); `available_day` es el día efectivo. |
| `ClientMeasurement` | FK → perfil; medidas, `body_fat_pct` / `muscle_mass_kg` opcionales del cliente (solo API) y `bioimpedance`; `source=client\|advisor` (quién la creó); `hidden_by_advisor`. Una fila por cliente y fecha (`client_measurement_profile_day`). |
| `ClientProgressPhoto` | FK → perfil; frente, espalda y lado; `source`; `hidden_by_advisor`. Una fila por cliente y fecha (`client_photo_profile_day`). `save()` pasa cada hueco por `core.utils.files.process_image_field_if_changed`, como los demás modelos con imágenes: WebP (calidad 80, máx. 1280 px) y, al sustituir un hueco, se borra su archivo anterior (celda web y API). |
| `ClientAccessRequest` | FK → perfil; `kind` primer acceso o continuidad; `order_number` / `purchase_date` opcionales. |

Todo cuelga de `ClientProfile` con `CASCADE`: al borrar el
contacto se borra su área de cliente completa (ver el README de `communication`). Los FK a
`BoardItem` son `SET_NULL`: si se borra el elemento del board, la fila se queda sin él. Las
excepciones son `ClientProgramFile.board_item` (`CASCADE`): una celda siempre tiene archivo, así que
borrar el elemento vacía la celda; y `ClientLesson.template_item` (`CASCADE`): borrar un contenido de
academia de una plantilla lo quita a todos los clientes.

### Ciclo del programa

| Estado | Condición | Acceso del cliente |
|---|---|---|
| Borrador | `start_date` es `null` | No cambia |
| Programado | `hoy < start_date` y `deactivated_at` vacío | `active` (se concede al activar; la app muestra "Tu programa inicia …") |
| Activo | `start_date <= hoy <= start_date + duration_days` y `deactivated_at` vacío | `active` (se concede al activar) |
| Terminado | `deactivated_at` relleno (asesor, expiración horaria o fin del add-on) | `none` ("Sin acceso") |

Un programa programado o activo está **en curso** (`assignment_is_running`, `assignment.is_running`).

- **Activar** (`activate_program`) guarda la fecha de inicio y la duración, acepta las solicitudes
  de acceso pendientes (`access_actions.grant_access_for_program`) o, si no hay, activa el perfil, y
  deja una nota en `ActivityContact`.
- **Fechas bloqueadas.** Mientras el programa está en curso, ni la fecha de inicio ni
  `duration_days` cambian: `ProgramPeriodForm(assignment=...)` pinta los dos campos desactivados (se
  ignora lo que llegue en el POST) y `activate_program` lanza `ValueError`. Solo **Desactivar** (o
  que llegue su fin) lo para.
- **Desactivar / expirar.** `deactivate_program` y la tarea horaria `expire_due_programs` (cuando
  el último día ya terminó en la zona del cliente) rellenan
  `deactivated_at` y llaman a `clear_access_on_program_end` (`access_status=none`); el siguiente
  login en Fam Fit crea una nueva solicitud `first_access`.
- **La renovación conserva los datos.** Las herramientas siempre editan la **asignación de trabajo**
  (`get_or_create_working_assignment`): la última del cliente, haya terminado o no; solo un cliente
  sin ninguna recibe un borrador nuevo. Volver a activar un programa terminado (desde Progreso o
  Aceptar) pone el nuevo periodo en la misma asignación, así que la tabla Programa, los productos y
  la academia se mantienen hasta que el asesor los cambie, y la app sigue mostrando los últimos
  archivos. Al expirar o desactivar no se borra nada.
- **Las lecciones desbloqueadas se mantienen.** Una renovación reinicia el día del programa, pero
  antes `activate_program` guarda en `unlocked_through_day` el día alcanzado en el periodo que
  termina (`reached_program_day`). `lesson_is_unlocked` abre una lección si
  `unlock_day <= unlocked_through_day` o si el día actual ya llegó, así que lo ya desbloqueado sigue
  abierto y el resto sigue la nueva cuenta. Vive en la asignación del cliente: las plantillas y el
  contenido del board no se tocan.
- **Aceptar una solicitud** (`start_program_for_request`). **Aceptar** (panel) y **Admitir** (home)
  abren el mismo formulario (`client-area-accept-request-form.html`) en un collapse de Bootstrap
  debajo de la solicitud, con la fecha de inicio y la duración. Por defecto: el hoy del cliente
  (`local_today()`) y `proposed_duration_days`, es decir, la duración del propio programa
  (también si ya terminó); si no tiene, la del último programa iniciado; y si tampoco, la del modelo
  (90). Al confirmar se activa la asignación de trabajo (la misma en una renovación) con
  `activate_program`, que además acepta la solicitud. Si el programa está en curso (activo o
  programado), sus fechas siguen bloqueadas y solo se acepta la solicitud (sin 422).

### Fechas locales

El servidor (`TIME_ZONE`, `Europe/Madrid`, también el de Celery), el asesor (zona del navegador que
activa en cada petición `users.middle.TimezoneFromSessionMiddleware`) y el cliente pueden estar en
zonas distintas. Nunca `date.today()`:

- **El calendario del cliente** es `ClientProfile.local_today()`, en `ClientProfile.time_zone` (lo
  manda Fam Fit en `X-Timezone` y lo guarda `client_api.auth.remember_client_timezone`; vacío usa
  `TIME_ZONE`). De él salen el día del programa, los días restantes, el progreso, si está
  programado / activo / terminado (`services.programs`, `on` por defecto), las lecciones
  desbloqueadas, el día de los registros (Añadir, el valor por defecto de la API y su "como mucho
  mañana"), la fecha de inicio propuesta, la expiración horaria y los avisos de las 08:00. Así el
  asesor y la app ven el mismo día.
- **La fecha del asesor** (`timezone.localdate()`) se queda para lo que fecha el asesor: productos,
  filas de Programa, notas y el filtro de la lista de contactos por estado del programa (una sola
  fecha en el SQL de la lista).

### Tablas Evolución / Fotos

- **Una fila por cliente y fecha** (el registro entero, no un valor suelto), compartida por el
  asesor y la app Fam Fit. La migración `0015` fusionó los duplicados que había (ver
  [Migraciones](#migraciones)).
- **Añadir** (`add_record_row`) crea una fila vacía con el día siguiente a la última fila del
  cliente en esa tabla (también las **ocultas por el asesor**, que conservan su fecha), o con el hoy
  del cliente (`local_today()`) si no hay ninguna. Nunca usa una fecha ocupada, así que siempre
  funciona.
- Cada fila es el formulario de su registro (`services.pane.build_record_forms`,
  `ClientMeasurementForm` / `ClientProgressPhotoForm` con `RecordCellFormMixin`): cada celda
  (`client-area-record-cell.html`) es un formulario pequeño que se envía en `change`, guarda solo su
  campo en ese mismo registro y se reemplaza (`outerHTML`); un valor no válido vuelve con el error en
  la celda y un **200**. La celda de fecha se envía en `focusout`, porque el navegador lanza
  `change` con cada parte que se teclea de una fecha. Una fecha que ya usa otra fila del cliente
  muestra "Ya existe un registro para esa fecha" (con "eliminado del panel, el cliente aún lo ve" si
  esa fila está oculta) y no se guarda; una fecha nueva válida devuelve la tabla entera con
  `HX-Retarget` a la tabla (las filas se reordenan), así que sustituye la tabla y no la celda.
- Cada hueco de foto muestra su miniatura o un "+"; al pulsar cualquiera de los dos se sube (o se
  cambia) la foto.
- **Gráfica de Evolución**, debajo de la tabla de medidas: una línea por columna
  (`build_measurement_chart`: Peso, Pecho, Brazo, Cadera, Cintura, Pierna, con los nombres de
  `ClientMeasurementForm`; solo filas visibles y sin las celdas vacías). `client_area_tools.js` pide
  su JSON (`client_area_measurement_chart`) y la dibuja con ApexCharts (CDN, cargado en
  `contacts.html` como las estadísticas mensuales de la home); Desde / Hasta solo acotan el eje x.
  Cada cambio guardado en una tabla envía el evento `clientAreaRecordsChanged` (`{"kind": ...}`) en
  `HX-Trigger` (`views.RECORDS_CHANGED_EVENT`), y la gráfica se vuelve a pedir con los de
  `measurement`.
- El botón de añadir y el de borrar fila reutilizan `cotton/grid_add_button` y
  `cotton/grid_row_delete`, los mismos de la tabla Programa. Borrar una fila solo marca
  `hidden_by_advisor`.
- **Productos nutricionales** usan la misma tabla (`views.RECORD_GRIDS["product"]`,
  `ClientProductForm` con `CellFormMixin`, sin la regla de una fila por fecha): Añadir
  (`add_product_row`) inserta arriba una fila vacía y cada celda se guarda en `change`. Su fecha
  (hoy) solo ordena las filas: el formulario no tiene campo de fecha ni la tabla columna de fecha. Su borrar elimina la fila (`client_area_delete_product`). La API omite las filas cuyo
  nombre de producto sigue vacío.

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
- Se reutilizan con **Plantillas** (ver [Plantillas de academia](#plantillas-de-academia)). "Copiar
  de otro cliente" (`copy_academy_from_client`) sustituye todos los programas del cliente por una
  copia de los del otro (los programas de plantilla siguen apuntando a su plantilla, con los cambios
  del otro cliente).
- **Añadir contenido** añade un elemento propio solo de este cliente. Su enlace de YouTube y el
  adjunto subido se guardan en `Otros / <nombre del programa>` del board del asesor.

### Plantillas de academia

Una plantilla es una **carpeta directamente dentro de Videoteca** (las plantillas se crean en el
board, no en el panel). Cada elemento es un **Contenido de academia** del board (tipo `academy`, ver
el README de `apps/boards`): disponibilidad (Siempre / Día N, `BoardItem.unlock_day`), un enlace de
YouTube, un texto y un adjunto PDF / imagen, que se editan con `forms.AcademyContentForm`.

| Plantilla | Dónde | Quién puede asignarla |
|---|---|---|
| De sistema | Carpeta en la Videoteca del catálogo (`USER_ROOT`) | Cualquier asesor con acceso |
| Propia | Carpeta en la carpeta sombra de Videoteca del asesor | Solo ese asesor |

`services/academy.academy_template_folders(user)` las devuelve de la más nueva a la más antigua (el
board muestra Videoteca igual). "Añadir desde plantilla" (`add_program_from_template`) crea un
programa que apunta a la carpeta (`template_folder`, con su nombre) y activa la academia; no se puede
añadir la misma plantilla dos veces a un cliente.

La plantilla manda y se lee **en vivo**:

- `sync_template_lessons` crea la fila `ClientLesson` de cada contenido de academia de la carpeta (el id
  que usa la app) al mostrar el programa; lo que se añada después llega también a los clientes que ya
  la tenían.
- Editar un contenido (texto, enlace, adjunto, día por defecto) lo cambia para todos los clientes.
- Lo que se cambia para un cliente nunca toca la plantilla: la disponibilidad se guarda como cambio
  propio (`set_lesson_unlock_day`) y borrar un elemento de plantilla solo lo oculta a ese cliente
  (`hidden_by_advisor`). A un programa de plantilla también se le pueden añadir elementos propios.
- `program_lessons(program)` / `shown_lessons` devuelven lo que se muestra: los elementos de plantilla
  que siguen en la carpeta (en el orden del mosaico) y después los propios. Un contenido que se saca de
  la carpeta deja de mostrarse; su fila conserva los cambios del cliente por si vuelve.

### Disponibilidad de la academia

Cada `ClientLesson` tiene su propia disponibilidad en `unlock_day` (`UNLOCK_DAY_ALWAYS = 0`):

| `unlock_day` | Etiqueta en el panel | Se abre |
|---|---|---|
| `0` | Siempre | Siempre, mientras la academia esté activada |
| `N >= 1` | Día N | Cuando `program_day >= N` |

Un elemento de plantilla sin cambio propio usa el `unlock_day` de su contenido;
`ClientLesson.available_day` es el valor efectivo que se usa aquí y en la API.

`todays_lesson` es la primera lección (programas y lecciones en orden) cuyo día coincide con
el día actual del programa; las de "Siempre" nunca lo son. La asignación solo guarda el interruptor No/Sí `academy_enabled`; no hay un
modo para toda la academia. La copia desde otro cliente conserva la disponibilidad de cada elemento.

### Servicios

| Módulo | Responsabilidad |
|---|---|
| `services/access.py` | Asignación de códigos de acceso únicos |
| `services/access_actions.py` | Aceptar solicitudes, activar/desactivar el acceso, darlo al iniciar el programa, quitarlo al terminar, textos de WhatsApp de continuidad |
| `services/entitlement.py` | `user_has_client_area(user)`: capability **o** `user_has_addon(user, CLIENT_AREA_ADDON_CODE)` |
| `services/profiles.py` | `get_or_create_client_profile`; "Mi perfil" de Fam Fit (`body_profile_values`, `missing_body_profile_fields`, `update_body_profile`) |
| `services/body.py` | Composición corporal de una fila de medidas: kcal diarias Mifflin-St Jeor, IMC y su categoría (el % de grasa y la masa muscular son solo los valores del cliente); niveles de actividad y rangos de valores |
| `services/programs.py` | Asignación de trabajo, `activate_program` / `deactivate_program`, `start_program_for_request`, fecha de fin, día del programa, progreso, estado en la tarjeta de contacto y filtro del listado |
| `services/content.py` | `upsert_measurement` / `upsert_progress_photo` (Fam Fit, un registro por fecha), `add_record_row`, `add_program_entry` / `set_program_file`, `add_product_row`, `hide_by_advisor` |
| `services/academy.py` | `set_academy_enabled`, `create_training_program`, `add_lessons(program, ...)`, `set_lesson_unlock_day`, `remove_lesson`, `academy_template_folders`, `add_program_from_template`, `sync_template_lessons`, `program_lessons`, `copy_academy_from_client`, `lesson_is_unlocked`, `todays_lesson` |
| `services/catalog.py` | Boards del área de clientes del asesor y búsqueda en el catálogo |
| `services/pane.py` | Contexto del panel, `build_catalog_context`, `build_measurement_chart` (series de la gráfica de Evolución), URLs de WhatsApp |
| `services/inbox.py` | `pending_access_requests_for_advisor` (de la más reciente a la más antigua, con contacto, URL de WhatsApp y antigüedad) para el bloque del home; `HOME_ACCESS_REQUESTS_LIMIT = 3` |
| `services/expiry.py` | Expiración horaria y `pause_programs_without_entitlement` |

## Board del catálogo

El asesor trabaja con **un solo** board, "Área de clientes" (`CLIENT_AREA_OWN_BOARD_TITLE`): su board
privado del área de clientes, que en sus vistas incorpora en solo lectura el catálogo de sistema de
FAM TEAM. Almacenamiento, permisos y carpetas sombra están en el README de `apps/boards` ("Boards del
área de clientes").

| Parte | Dueño | Tipos permitidos | Qué puede hacer el asesor |
|---|---|---|---|
| Catálogo de sistema (Nutrición, Deporte, Videoteca, Otros) | `USER_ROOT` | PDF, imagen; Videoteca: solo plantillas (carpetas, con contenidos de academia dentro) | Verlo y elegir elementos; añadir los suyos y subcarpetas dentro de sus carpetas (carpetas sombra) |
| Contenido propio | Asesor | Carpetas, texto, imagen, PDF, YouTube; Videoteca: solo sus plantillas | CRUD completo dentro de las carpetas del catálogo; nada en la raíz del board |

- `services/pane.build_catalog_context` devuelve `catalog_board` (el board propio).
  `.client-area-tools` lleva su id y la URL de `board_mosaic_data`; el selector de
  `client_area_tools.js` abre ese mosaico combinado, con botón de volver dentro de las carpetas.
  Las fichas de solo lectura se pueden elegir, y lo marcado se mantiene al cambiar de carpeta y al
  buscar.
- `search_client_area_catalog` filtra el índice Redis de boards a esos dos boards y pinta los
  resultados con `textContent`.
- `CatalogItemFormMixin` limita sus `catalog_fields` a
  `get_client_area_catalog_boards_queryset(asesor)`, así que no entra ningún elemento de otro board.
- Los vídeos subidos (contenido antiguo: los vídeos solo son de YouTube) y los contenidos de academia
  (viven en su plantilla) nunca se ofrecen: el formulario, la búsqueda del catálogo y las fichas del
  selector (`client_area_tools.js`) excluyen `CLIENT_AREA_PICKER_EXCLUDED_ITEM_TYPES`.
- El widget del campo es `widgets.CatalogPickerInput`: un botón "Añadir desde board" y el id oculto
  que escribe `client_area_tools.js`, por nombre de campo (caben varios selectores en un
  formulario). Cada selector elige un elemento.

| Herramienta | Selector |
|---|---|
| Celda del programa (`ProgramCellForm.board_item`, "Desde board" en el menú de la celda; abre la carpeta de la columna y guarda al elegir) | Un elemento |
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
| Academia (elemento propio): enlace de YouTube, adjunto | Otros / `<nombre del programa>` (la subcarpeta se crea con la primera subida) |

`const.PROGRAM_SLOT_FOLDERS` relaciona cada hueco con su carpeta. Videoteca solo guarda plantillas. La
subcarpeta de Otros se busca
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
| `access/activate/` · `deactivate/` | `client_area_activate_access`, `client_area_deactivate_access` | Parcial de herramientas |
| `records/<kind>/add/` (`kind` = `measurement` \| `photo` \| `product`, `views.RECORD_GRIDS`) | `client_area_add_record` | Parcial de la tabla |
| `records/<kind>/<id>/<field>/` | `client_area_set_record_field` | La celda (errores en la celda, 200), o la tabla (`HX-Retarget`) tras cambiar la fecha |
| `records/<kind>/<id>/hide/` | `client_area_hide_record` | Parcial de la tabla |
| `records/measurement/chart/` (GET) | `client_area_measurement_chart` | JSON `{"series": [{"name", "data": [[fecha, valor], ...]}]}` de la gráfica de Evolución |
| `program/entries/add/` | `client_area_add_program_entry` | Parcial de la tabla del programa (fila nueva) |
| `program/entries/<id>/<slot>/` | `client_area_set_program_file` | `ProgramCellForm` (`file` o `board_item`): parcial de la tabla del programa; toast 422 si no es válido, 404 si el hueco no existe |
| `program/files/<id>/delete/` · `program/entries/<id>/delete/` | `client_area_delete_program_file`, `client_area_delete_program_entry` | Parcial de la tabla del programa |
| `products/<id>/delete/` | `client_area_delete_product` | Parcial de la tabla |
| `academy/` (GET) | `client_area_academy` | Sección de academia con las carpetas de programas |
| `academy/toggle/` | `client_area_toggle_academy` | Sección de academia (el programa enviado en `program_id` sigue abierto) |
| `academy/programs/add/` | `client_area_add_training_program` | Sección de academia con el programa nuevo abierto; toast 422 si el nombre no es válido |
| `academy/programs/<id>/` (GET) | `client_area_training_program` | Sección de academia con el programa abierto |
| `academy/programs/<id>/rename/` · `delete/` | `client_area_rename_training_program`, `client_area_delete_training_program` | Sección de academia (abierto / carpetas) |
| `academy/programs/<id>/lessons/add/` | `client_area_add_lesson` | GET: formulario para el modal; POST: tabla de lecciones, o el formulario con errores |
| `academy/lessons/<id>/availability/` | `client_area_set_lesson_availability` | Tabla de lecciones; toast 422 si el dato no es válido |
| `academy/lessons/<id>/delete/` | `client_area_delete_lesson` | Tabla de lecciones |
| `academy/templates/add/` · `copy/` | `client_area_add_academy_template`, `client_area_copy_academy` | Sección de academia (el programa nuevo abierto / carpetas); toast 422 si la plantilla ya está en la academia del cliente |
| `program/activate/` · `program/deactivate/` | `client_area_activate_program`, `client_area_deactivate_program` | Parcial de herramientas; si el periodo no es válido se vuelve a pintar `#caProgressSection` |
| `access-requests/` | `client_area_access_requests` | Parcial con la lista completa para el modal "Ver todas" del home |
| `access-requests/<id>/accept/` | `client_area_accept_access` | GET: formulario de aceptar (`?scope=pane\|home\|modal`). POST: parcial de herramientas (panel) o bloque del home + lista del modal (OOB); `showToast`. Periodo no válido: se vuelve a pintar el formulario con 200 |
| `catalog/search/` | `client_area_catalog_search` | Resultados de búsqueda en JSON |

### Modal de formulario compartido

- Los elementos de academia se añaden con un botón
  **Añadir contenido** que abre `#clientAreaFormModal` (`components/modals/client-area-modals.html`, incluido
  en `contacts.html` fuera de `#contactModal`, junto al selector del catálogo).
- `data-ca-open-form` lo abre con `Modal.show()` y no con `data-bs-toggle`, para que
  `#contactModal` no se cierre. El parcial del formulario (`client-area-tool-form.html`) rellena el
  cuerpo y fija el título con `hx-swap-oob`.
- Si se guarda bien, la vista solo reemplaza el parcial de la tabla y envía `showToast` +
  `clientAreaFormSaved` (cierra el modal). Con errores, el formulario se vuelve a pintar dentro del
  modal con un **200** (`HX-Retarget`).
- Los modales de alta son de una columna. `cotton/tool_add_button` recibe el `url` del formulario (los
  elementos de academia del programa abierto).
- **Secciones del formulario.** Los campos llevan los attrs de sección del repo (`data_section` /
  `data_section_label`, como en `components/form-model.html`). `client-area-tool-form.html` pinta
  el título de la sección cuando cambia, y `cotton/form_field` oculta la etiqueta del campo dentro de
  una sección (la etiqueta es el título).

### Secciones del panel

- **Confirmaciones** — cada `hx-confirm` dentro de `.client-area-tools` abre el modal global
  `#globalConfirmModal` (`openGlobalConfirmModal`, `static/js/global_confirm.js`) en vez del
  diálogo del navegador: un listener de `htmx:confirm` en `client_area_tools.js` lanza la petición al
  confirmar.
- **Acceso** — código de acceso con copiar, aceptar solicitud (fecha de inicio y duración, ver
  arriba), activar/desactivar el acceso, enlace
  de WhatsApp y badges de App Store / Play Store (provisionales).
- **Evolución / Fotos** — con scroll horizontal y edición en la propia tabla (ver *Tablas Evolución
  / Fotos*); Evolución tiene además su gráfica con rango Desde / Hasta. Borrar una fila (la haya creado el cliente o el asesor) solo marca `hidden_by_advisor`: desaparece del panel, pero la API de Fam Fit la sigue
  devolviendo.
- **Productos nutricionales** — Productos y Explicación (el campo `observations`, la columna más
  ancha, `.ca-col-wide`), editados en la propia tabla como
  Evolución (ver *Tablas Evolución / Fotos*). Borrar elimina la fila. La API lee los productos en
  directo, sin caché.
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
  **Plantillas** ("Añadir desde plantilla", con las plantillas de Videoteca que este cliente aún no
  tiene, y "Copiar de otro cliente", con `hx-confirm`); un programa de plantilla lleva un icono de
  colección. Abierta: botón de volver, renombrar en línea, borrar (`hx-confirm`), la tabla de
  elementos y **Añadir contenido**. Los elementos de plantilla muestran el título o el texto de su
  contenido con un icono de colección; su disponibilidad y su borrado solo afectan a este cliente.
  **Añadir contenido** abre `ClientLessonForm`, de una columna y por secciones:

  | Sección | Campos |
  |---|---|
  | Disponibilidad | `widgets.AvailabilityWidget`: casilla "Siempre" con el campo "Día" a su derecha (se envían como `unlock_day_always` / `unlock_day`). Marcar Siempre desactiva el día (`client_area_tools.js`); `AvailabilityField` exige un día ≥ 1 salvo con Siempre |
  | Contenido | `youtube_url`, validado con `extract_youtube_video_id`. Los vídeos solo son enlaces de YouTube: no se suben vídeos |
  | Texto | `text` |
  | Adjuntar archivo (PDF, imagen) | `attachment_source`: Subir archivo (`attachment_file`) / Desde board (`attachment_item`, PDF o imagen) |

  Los campos con `data-ca-when="<origen>=<valor>"` solo se ven con esa opción marcada; `clean()`
  descarta el de la opción no marcada y exige algún contenido. `add_lessons` crea un elemento con el
  enlace, el texto y el adjunto. Cada fila tiene el mismo widget de disponibilidad,
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
- **Admitir**, desde el bloque o desde el modal, abre el formulario de aceptar debajo de la fila
  (ver *Aceptar una solicitud*). Al confirmar hace POST a `client_area_accept_access`, que inicia el
  programa y devuelve el bloque (se reemplaza con `outerHTML`) junto con la lista del modal en
  `hx-swap-oob`, más un `showToast`. Si la solicitud ya no está pendiente, toast con 422.
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
| `0015_records_by_date_and_renewals` | Añade `ClientProgramAssignment.unlocked_through_day`. Datos (modelos históricos): fusiona las medidas / fotos duplicadas de un cliente y fecha en la fila más reciente, con el último valor no vacío de cada campo / hueco (queda oculta solo si lo estaban todas); en clientes con varios programas, el último toma las filas de la tabla Programa, los productos y la academia que le falten del programa anterior más reciente que los tenga, y `unlocked_through_day` de los periodos anteriores. Después, único (`client_profile`, `recorded_on`) en los dos modelos. Los archivos de fotos de los duplicados borrados que la fila fusionada no conserva se borran del storage |
| `0016_clientprofile_time_zone` | Añade `ClientProfile.time_zone` |
| `0017_client_body_composition` | Añade `ClientProfile.sex` / `height_cm` / `neck_cm` / `activity_level` y `ClientMeasurement.body_fat_pct` / `muscle_mass_kg`. Datos: un `bioimpedance.body_fat_pct` (2–75) / `muscle_mass_kg` (10–150) numérico se copia a su campo |
| `0018_remove_clientprofile_neck_cm` | Elimina `ClientProfile.neck_cm` (el % de grasa ya no se calcula) |
| `0019_academy_templates` | Añade `TrainingProgram.template_folder` y `ClientLesson.template_item` / `hidden_by_advisor`; `ClientLesson.unlock_day` pasa a admitir vacío (necesita la `0013` de `boards`) |
| `0020_academy_plans_to_videoteca` | Datos (modelos históricos), ver abajo |
| `0021_remove_academy_plans` | Elimina `ClientLesson.source_item`, `TrainingProgram.source_plan`, `AcademyPlanItem` y `AcademyPlan`; añade las restricciones únicas de plantillas |

La `0020` convierte las plantillas antiguas en plantillas de Videoteca:

1. Las subcarpetas que ya había en Videoteca guardaban lo subido desde el panel para cada cliente, no
   plantillas: pasan a Otros (la carpeta del catálogo o la carpeta sombra del asesor, que se crea si
   falta) con sus elementos.
2. Cada `AcademyPlan` pasa a ser una carpeta con su nombre y la fecha de su `updated_at`: en la
   Videoteca del catálogo si es de `USER_ROOT` y, si no, en la Videoteca propia del asesor (se crea su
   board si falta). Cada `AcademyPlanItem` pasa a ser un contenido de academia con su `unlock_day` y
   su `order`: un YouTube da el enlace, un texto se suma al texto del elemento y un PDF / imagen /
   vídeo subido pasa a ser el adjunto si no había otro. Los archivos se comparten por ruta, no se copian.
3. Cada programa con `source_plan` apunta a su carpeta; una segunda copia de la misma plantilla en el
   mismo cliente se queda como programa propio. Sus lecciones de la plantilla pasan a ser elementos
   de plantilla que solo guardan la disponibilidad si es distinta de la de la plantilla; los elementos
   que el cliente ya no tenía se añaden ocultos. Los elementos propios no se tocan.

Sin catálogo no hace nada. Al revertir, los elementos de plantilla pasan a ser elementos propios de
su contenido de academia (los ocultos se borran); las plantillas antiguas no se reconstruyen. Los
`AcademyPlanItem` guardados desde asignaciones en modo "all" conservaron el día que tenían (`0005`). El
contenido propio de las lecciones en los campos que borra `0011` (URL de vídeo, vídeo, adjunto) no se
convierte en elementos del board.

## Configuración y dependencias

Dependencias: `communication`, `boards`, `users`, `user_levels`, `pricing`. El add-on, sus precios por
nivel y el checkout de Stripe viven en `pricing` (`Addon` con código `client_area`, sembrado por la
migración `0003` de `pricing`). Los archivos van por el backend de almacenamiento global.

| Servicio | Uso |
|---|---|
| Celery beat | `client_area.tasks.expire_client_programs_task` cada hora a los :15 (el día de cada cliente termina a su medianoche) |
| Celery | `client_area.tasks.pause_lapsed_client_programs_task` (fin del add-on) |
| Redis | La búsqueda del catálogo reutiliza el índice de búsqueda de boards |

No tiene integración propia con Sentry.
