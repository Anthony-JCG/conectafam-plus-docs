# client_area

## Description

Advisor-side **client area**: nutrition/sport programs, access codes, measurements, progress photos,
nutritional products and the academy of each client. Consumers are `ClientProfile` rows linked to a
`communication.Contact`, not `users.User` nodes in the sponsor tree. The Fam Fit native app reads
this data through [`apps/client_api`](../client_api/README.md).

Relationship to the core apps:

- **`user_levels`** — `CLIENT_AREA_MODEL_KEY` + `ACCESS_ACTION_KEY`. Leader and Leader Pro are
  allowed; Basic/Pro are denied there. `user_has_client_area` also accepts the purchased
  `client_area` add-on (`pricing.UserAddon`).
- **`communication`** — `ClientProfile.contact` is OneToOne to `Contact`. Program start/end writes
  `ActivityContact` notes. The pane lives in the contact modal's **Área de cliente** tab.
- **`boards`** — program files and academy lessons reference a `BoardItem` of the advisor's
  client-area board; manual uploads are stored there first (see [Catalog board](#catalog-board)
  and [Board storage](#board-storage)).
- **`pricing`** — sells the add-on; its end pauses the advisor's programs
  (see [Add-on lapse](#add-on-lapse-programs-paused)).
- **`users.User`** — the advisor (owner of the contact and of their own academy templates). The
  client is never this user.

## Models and Data

| Model | Relationships and fields |
|---|---|
| `ClientProfile` | OneToOne → `communication.Contact`. Unique `access_code`, `access_status` (`none` / `pending` / `active` / `deactivated`), `time_zone` (device IANA zone, see [Local dates](#local-dates)). Fam Fit "Mi perfil": `sex` (`male` / `female`), `height_cm`, `activity_level` (1–5); the birth date is `contact.date_of_birth`. API only, not in the web pane. |
| `ClientProgramAssignment` | FK → `ClientProfile`. `start_date`, `duration_days`, `deactivated_at`, `academy_enabled`, `unlocked_through_day` (program day reached in previous periods). The end date is derived (`start_date + duration_days`), never stored. Reused on every renewal. |
| `ClientProgramEntry` | Row of the Programa table: FK → assignment (`program_entries`); `assigned_on` (defaults to `timezone.localdate`). Ordered newest first (`-assigned_on`, `-pk`). |
| `ClientProgramFile` | One cell: FK → entry (`files`); slot `nutrition` / `sport` / `other`, unique per entry; FK → `BoardItem` (the file; uploads become board items). |
| `ClientProduct` | FK → assignment; `recorded_on`, `products`, `observations`. Plain text, no board item. |
| `TrainingProgram` | Programa formativo: FK → assignment (`training_programs`); optional FK → `boards.BoardFolder` (`template_folder`, `SET_NULL`: the Videoteca template it reads); `name`, `order`. One Academia folder. A template is in a client's academy at most once (`training_program_assignment_template`). |
| `ClientLesson` | FK → `TrainingProgram` (`lessons`); one academy element, ordered by `order`, `pk`. **Own element**: `board_item` (YouTube content), `text`, `attachment_item` (PDF / image board item), `unlock_day`. **Template element**: FK → `BoardItem` (`template_item`, `CASCADE`) whose content it reads; it only stores the client's overrides, `unlock_day` (`null` = the template's) and `hidden_by_advisor`. One row per program and template item (`client_lesson_program_template_item`); `available_day` is the effective day. |
| `ClientMeasurement` | FK → profile; body metrics, the client's optional `body_fat_pct` / `muscle_mass_kg` (API only) and `bioimpedance`; `source=client\|advisor` (who created it); `hidden_by_advisor`. One row per client and date (`client_measurement_profile_day`). |
| `ClientProgressPhoto` | FK → profile; front/back/side; `source`; `hidden_by_advisor`. One row per client and date (`client_photo_profile_day`). `save()` runs `core.utils.files.process_image_field_if_changed` on each slot like the other image models: WebP (quality 80, max 1280 px) and a replaced slot deletes its previous file (web cell and API). |
| `ClientAccessRequest` | FK → profile; `kind` first access / continuity; optional `order_number` / `purchase_date`. |

Everything hangs from `ClientProfile` with `CASCADE`, so
deleting the contact deletes its whole client area (see the `communication` README). FKs to
`BoardItem` are `SET_NULL`: deleting a board item leaves the row without it. The exceptions are
`ClientProgramFile.board_item` (`CASCADE`): a cell always holds a file, so deleting the item empties
the cell; and `ClientLesson.template_item` (`CASCADE`): deleting an academy content of a template
removes it from every client.

### Program lifecycle

| State | Condition | Client access |
|---|---|---|
| Draft | `start_date` is `null` | Unchanged |
| Scheduled | `today < start_date`, `deactivated_at` null | `active` (granted on activation; the app shows "Tu programa inicia …") |
| Active | `start_date <= today <= start_date + duration_days`, `deactivated_at` null | `active` (granted on activation) |
| Ended | `deactivated_at` set (advisor, hourly expiry or add-on lapse) | `none` ("Sin acceso") |

Scheduled and active programs are **running** (`assignment_is_running`, `assignment.is_running`).

- **Activate** (`activate_program`) stores the start date and duration, accepts pending access
  requests (`access_actions.grant_access_for_program`) or activates the profile, and writes an
  `ActivityContact` note.
- **Period lock.** While the program runs, the start date and `duration_days` are fixed:
  `ProgramPeriodForm(assignment=...)` renders both disabled (posted values are ignored) and
  `activate_program` raises `ValueError`. Only **Desactivar** (or its end) stops it.
- **Deactivate / expire.** `deactivate_program` and the hourly `expire_due_programs` (once the last
  day is over in the client's zone) set
  `deactivated_at` and call `clear_access_on_program_end` (`access_status=none`); the next Fam Fit
  login creates a new `first_access` request.
- **Renewal keeps the data.** Tools always edit the **working assignment**
  (`get_or_create_working_assignment`): the client's latest assignment, ended or not; only a client
  without one gets a new draft. Activating an ended program again (Progreso or Aceptar) sets the new
  period on the same assignment, so the Programa grid, products and academy persist until the
  advisor changes them, and the app keeps showing the latest files. Nothing is deleted on expiry or
  deactivation.
- **Unlocked lessons persist.** A renewal restarts the program day, but `activate_program` first
  stores the day reached in the ending period (`reached_program_day`) in `unlocked_through_day`.
  `lesson_is_unlocked` opens a lesson when `unlock_day <= unlocked_through_day` or the current day
  reached it, so already unlocked lessons stay open and the rest follow the new count. It lives on
  the client's assignment: templates and board content are never touched.
- **Accept a request** (`start_program_for_request`). **Aceptar** (pane) and **Admitir** (home)
  open the same inline form (`client-area-accept-request-form.html`) in a Bootstrap collapse under
  the request, with the start date and duration. Defaults: the client's today (`local_today()`) and
  `proposed_duration_days`: the program's own (also after it ended), else the latest started
  program's, else the model default (90). Confirming activates the working assignment (the same one
  on a renewal) with `activate_program`, which also accepts the request. If the program is running
  (active or scheduled), its period stays locked and only the request is accepted (no 422).

### Local dates

The server (`TIME_ZONE`, `Europe/Madrid`, also Celery's), the advisor (browser zone activated per
request by `users.middle.TimezoneFromSessionMiddleware`) and the client can be in different zones.
Never `date.today()`:

- **The client's calendar** is `ClientProfile.local_today()`, in `ClientProfile.time_zone` (sent
  by Fam Fit in `X-Timezone`, stored by `client_api.auth.remember_client_timezone`; empty uses
  `TIME_ZONE`). It drives program day, days remaining, progress, scheduled / active / ended
  (`services.programs`, default `on`), unlocked lessons, the records' day (Añadir, the API
  default and its "at most tomorrow" check), the proposed start date, the hourly expiry and the
  08:00 reminders. Advisor and app therefore see the same day.
- **The advisor's date** (`timezone.localdate()`) stays for what the advisor dates: products,
  Programa rows, notes, and the contact list filter by program status (one SQL date for the list).

### Evolución / Fotos tables

- **One row per client and date** (the whole record, not a single value), shared by the advisor
  and the Fam Fit app. Migration `0015` merged the existing duplicates (see [Migrations](#migrations)).
- **Añadir** (`add_record_row`) adds an empty row dated the day after the client's latest row of
  that table (rows **hidden by the advisor** included, they keep their date), or the client's today
  (`local_today()`) when there is none. It never takes a used date, so it always works.
- Each row is its record form (`services.pane.build_record_forms`, `ClientMeasurementForm` /
  `ClientProgressPhotoForm` with `RecordCellFormMixin`): every cell
  (`client-area-record-cell.html`) is a small form posted on `change` that saves only its field
  of that same record and swaps the cell back (`outerHTML`); invalid values come back inline with
  **200**. The date cell posts on `focusout` instead, since browsers fire `change` on every typed
  segment of a date input. A date already used by another row of the client shows "Ya existe un
  registro para esa fecha" (with "eliminado del panel, el cliente aún lo ve" when that row is
  hidden) and is not saved; a new valid date returns the whole table with `HX-Retarget` to the
  table (the rows are reordered), so it replaces the table, not the cell.
- Photo slots show their thumbnail or a "+"; clicking either uploads (or replaces) the slot.
- **Evolución chart** below the measurements table: one line per column (`build_measurement_chart`:
  Peso, Pecho, Brazo, Cadera, Cintura, Pierna, named from `ClientMeasurementForm` labels; visible
  rows only, empty cells skipped). `client_area_tools.js` fetches its JSON
  (`client_area_measurement_chart`) and draws it with ApexCharts (CDN, loaded by `contacts.html`
  like the home's monthly stats); Desde / Hasta only narrow the x axis. Every saved change of a
  grid sends the `clientAreaRecordsChanged` event (`{"kind": ...}`) in `HX-Trigger`
  (`views.RECORDS_CHANGED_EVENT`), and the chart refetches on `measurement` ones.
- The add button and the row delete reuse `cotton/grid_add_button` and `cotton/grid_row_delete`,
  shared with the Programa table. Deleting a row only sets `hidden_by_advisor`.
- **Productos nutricionales** use the same grid (`views.RECORD_GRIDS["product"]`, `ClientProductForm`
  with `CellFormMixin`, no one-row-per-date rule): Añadir (`add_product_row`) inserts an empty row
  on top and each cell is saved on `change`. Its date (today) only orders the rows: the form has
  no date field and the table no date column. Its delete removes the row
  (`client_area_delete_product`). The API skips rows whose product name is still empty.

### Programa table

- Each `ClientProgramEntry` is a row (date + one cell per column); the client always gets the
  **latest file of each column**: the newest non-empty cell by row date, then row id. That is what
  the Fam Fit `/program/` endpoint returns (see the `client_api` README).
- **Nuevo programa** (`add_program_entry`) adds an empty row dated today.
- `set_program_file(entry, slot, ...)` fills or replaces a cell with an upload (stored in the
  column's board folder, see [Board storage](#board-storage)) or a picked board item, and re-dates
  the row to today.
- Removing a cell or a row deletes only the program rows; the board items stay in the board.

### Academia: programas formativos

Academia is a set of **programas formativos** (`TrainingProgram`), shown as folders; opening one
lists its elements (`ClientLesson`) and manages them. Programs can be created, renamed and deleted
(deleting removes its elements; their board items stay in the board). The No/Sí
`academy_enabled` toggle stays on the assignment and covers every program.

Programs belong to the **client's assignment**, not to the advisor:

- Availability is relative to each client's program day, like the lessons already were.
- Reuse goes through **Plantillas** (see [Academy templates](#academy-templates)). "Copiar de otro
  cliente" (`copy_academy_from_client`) replaces every program of the client with a copy of the
  other client's programs (template programs keep their template and the other client's overrides).
- **Añadir contenido** adds an own element of this client only. Its YouTube link and uploaded
  attachment are stored in `Otros / <program name>` of the advisor's board.

### Academy templates

A template is a **folder right inside Videoteca** (the board, not the pane, is where templates are
made). Each of its elements is a **Contenido de academia** board item (`academy` type, see the
`apps/boards` README): availability (Siempre / Día N, `BoardItem.unlock_day`), a YouTube link, a
text and a PDF / image attachment, edited with `forms.AcademyContentForm`.

| Template | Where | Who can assign it |
|---|---|---|
| System | Folder in the catalog Videoteca (`USER_ROOT`) | Every entitled advisor |
| Own | Folder in the advisor's shadow folder of Videoteca | Only that advisor |

`services/academy.academy_template_folders(user)` lists them newest first (the board shows
Videoteca the same way). "Añadir desde plantilla" (`add_program_from_template`) creates a program
pointing at the folder (`template_folder`, named like it) and enables the academy; adding the same
template twice to a client is rejected.

The template is the source of truth and is read **live**:

- `sync_template_lessons` gives each academy content of the folder its `ClientLesson` row (the id the
  app uses) when the program is shown; contents added later reach clients already assigned.
- Editing a content (text, link, attachment, default day) changes it for every client.
- Per-client changes never touch the template: the availability is stored as an override
  (`set_lesson_unlock_day`), and deleting a template element hides it for that client
  (`hidden_by_advisor`). Own elements can be added to a template program as well.
- `program_lessons(program)` / `shown_lessons` return the elements to show: template elements still in
  the folder (in its mosaic order), then own elements. A content moved out of the folder stops
  showing; its row keeps the client's overrides in case it comes back.

### Academy availability

Each `ClientLesson` has its own availability in `unlock_day` (`UNLOCK_DAY_ALWAYS = 0`):

| `unlock_day` | Pane label | Unlocked when |
|---|---|---|
| `0` | Siempre | Always, while the academy is enabled |
| `N >= 1` | Día N | `program_day >= N` |

A template element without an override uses its content's `unlock_day`; `ClientLesson.available_day`
is the effective value used below and by the API.

`todays_lesson` is the first lesson (programs and lessons in order) whose day equals the
current program day; "Siempre" lessons never are. The assignment only keeps the No/Sí `academy_enabled` toggle; there is no academy-wide
mode. Copy-from-client keeps each element's availability.

### Services

| Module | Responsibility |
|---|---|
| `services/access.py` | Unique access-code allocation |
| `services/access_actions.py` | Accept requests, activate/deactivate access, grant on program start, clear on program end, continuity WhatsApp texts |
| `services/entitlement.py` | `user_has_client_area(user)`: capability **or** `user_has_addon(user, CLIENT_AREA_ADDON_CODE)` |
| `services/profiles.py` | `get_or_create_client_profile`; Fam Fit "Mi perfil" (`body_profile_values`, `missing_body_profile_fields`, `update_body_profile`) |
| `services/body.py` | Body composition of a measurement row: Mifflin-St Jeor daily kcal, BMI and its category (body fat % and muscle mass are only the client's values); activity levels and value ranges |
| `services/programs.py` | Working assignment, `activate_program` / `deactivate_program`, `start_program_for_request`, end date, program day, progress, contact status and list filter |
| `services/content.py` | `upsert_measurement` / `upsert_progress_photo` (Fam Fit, one record per date), `add_record_row`, `add_program_entry` / `set_program_file`, `add_product_row`, `hide_by_advisor` |
| `services/academy.py` | `set_academy_enabled`, `create_training_program`, `add_lessons(program, ...)`, `set_lesson_unlock_day`, `remove_lesson`, `academy_template_folders`, `add_program_from_template`, `sync_template_lessons`, `program_lessons`, `copy_academy_from_client`, `lesson_is_unlocked`, `todays_lesson` |
| `services/catalog.py` | Advisor's client-area boards and catalog search |
| `services/pane.py` | Tools pane context, `build_catalog_context`, `build_measurement_chart` (Evolución chart series), WhatsApp URLs |
| `services/inbox.py` | `pending_access_requests_for_advisor` (newest first, with contact, WhatsApp URL and age) for the home block; `HOME_ACCESS_REQUESTS_LIMIT = 3` |
| `services/expiry.py` | Hourly expiry and `pause_programs_without_entitlement` |

## Catalog board

The advisor works with **one** board, "Área de clientes" (`CLIENT_AREA_OWN_BOARD_TITLE`): their
private client-area board, whose views merge the FAM TEAM system catalog read-only. Storage,
permissions and shadow folders are described in the `apps/boards` README ("Client-area boards").

| Part | Owner | Allowed item types | Advisor can |
|---|---|---|---|
| System catalog (Nutrición, Deporte, Videoteca, Otros) | `USER_ROOT` | PDF, image; Videoteca: templates only (folders, academy contents inside) | View and pick; add own items and subfolders inside its folders (shadow folders) |
| Own content | Advisor | Folders, text, image, PDF, YouTube; Videoteca: own templates only | Full CRUD inside the catalog folders; nothing at the board root |

- `services/pane.build_catalog_context` returns `catalog_board` (the own board).
  `.client-area-tools` carries its id and `board_mosaic_data` URL; the picker in
  `client_area_tools.js` opens that merged mosaic, with a back button inside folders.
  Read-only tiles are selectable and the selection survives folder navigation and search.
- `search_client_area_catalog` filters the boards Redis index to the same two boards and renders
  results with `textContent`.
- `CatalogItemFormMixin` scopes its `catalog_fields` to
  `get_client_area_catalog_boards_queryset(advisor)`, so no item from another board is accepted.
- Uploaded videos (old content, videos are YouTube only) and academy contents (they live in their
  template) are never offered: `CLIENT_AREA_PICKER_EXCLUDED_ITEM_TYPES` is excluded by the form,
  the catalog search and the picker tiles (`client_area_tools.js`).
- The picker field widget is `widgets.CatalogPickerInput`: an "Añadir desde board" button plus the
  hidden id that `client_area_tools.js` writes, keyed by the field name (several pickers per form).
  Every picker takes one item.

| Tool | Picker |
|---|---|
| Program cell (`ProgramCellForm.board_item`, "Desde board" in the cell menu; opens the column's folder, saved on pick) | One item |
| Academy attachment (`ClientLessonForm.attachment_item`) | One PDF or image |
| Nutritional products | None |

### Board storage

Content uploaded from the pane (not picked from the board) is stored as a board item first, and
the program file or lesson references it: the board item is the source of truth.
`boards.services.client_area_uploads` resolves the folder: for an advisor, their shadow folder of
the catalog root folder (`ensure_shadow_folder`); for `USER_ROOT`, the catalog folder itself.

| Upload | Board folder |
|---|---|
| Programa, column Alimentación (`nutrition`) | Nutrición |
| Programa, column Deporte (`sport`) | Deporte |
| Programa, column Otros (`other`) | Otros |
| Academia (own element): YouTube link, attachment | Otros / `<program name>` (subfolder created on first upload) |

`const.PROGRAM_SLOT_FOLDERS` maps slots to folders. Videoteca only holds templates. The Otros
subfolder is resolved by name on each upload: renaming a program does not rename the folder (it may be shared with other clients'
programs of the same name); later uploads go to the new name.

## Add-on lapse: programs paused

When an advisor loses the client area (the `client_area` add-on subscription ends, or a downgrade
from Leader without the add-on), `services/expiry.pause_programs_without_entitlement(advisor)` runs
`deactivate_program` on every started, non-deactivated assignment: `deactivated_at` is set, the
client goes back to "Sin acceso" and an `ActivityContact` note is written. "Paused" is the ended
state above; products, files and academy stay on the assignment.

Triggers (`signals.py`, queued after commit as `tasks.pause_lapsed_client_programs_task`):

| Signal | Condition |
|---|---|
| `pricing.UserAddon` `post_save` | `is_active=False` for `client_area` (written by `sync_addon_subscription` on `customer.subscription.deleted` / `.updated`) |
| `user_levels.UserLevelProfile` `post_save` | Level changed |

The service checks `user_has_client_area` first, so an upgrade whose level already includes the
tool pauses nothing. Removing the content after a grace period is out of scope (future global
downgrade flow).

## Views and Frontend Integration

**This app uses HTMX.** `#pane-cliente` in the contact modal loads `load_client_area_pane`. Basic/Pro
users without the add-on see `RestrictedAccessAlert` `client_area_addon`, whose button posts to
`pricing.create_addon_checkout` with `client_area`.

URL prefix: **`/client-area/`**

| Endpoint | Name | Response |
|---|---|---|
| `load-pane/` | `load_client_area_pane` | Tools partial (`client-area-tools.html`) |
| `access/activate/` · `deactivate/` | `client_area_activate_access`, `client_area_deactivate_access` | Tools partial |
| `records/<kind>/add/` (`kind` = `measurement` \| `photo` \| `product`, `views.RECORD_GRIDS`) | `client_area_add_record` | Table partial |
| `records/<kind>/<id>/<field>/` | `client_area_set_record_field` | The cell (errors inline, 200), or the table (`HX-Retarget`) after a date change |
| `records/<kind>/<id>/hide/` | `client_area_hide_record` | Table partial |
| `records/measurement/chart/` (GET) | `client_area_measurement_chart` | JSON `{"series": [{"name", "data": [[date, value], ...]}]}` of the Evolución chart |
| `program/entries/add/` | `client_area_add_program_entry` | Program table partial (new row) |
| `program/entries/<id>/<slot>/` | `client_area_set_program_file` | `ProgramCellForm` (`file` or `board_item`): program table partial; 422 toast if invalid, 404 for an unknown slot |
| `program/files/<id>/delete/` · `program/entries/<id>/delete/` | `client_area_delete_program_file`, `client_area_delete_program_entry` | Program table partial |
| `products/<id>/delete/` | `client_area_delete_product` | Table partial |
| `academy/` (GET) | `client_area_academy` | Academy section with the program folders |
| `academy/toggle/` | `client_area_toggle_academy` | Academy section (keeps the program posted as `program_id` open) |
| `academy/programs/add/` | `client_area_add_training_program` | Academy section with the new program open; 422 toast on invalid name |
| `academy/programs/<id>/` (GET) | `client_area_training_program` | Academy section with the program open |
| `academy/programs/<id>/rename/` · `delete/` | `client_area_rename_training_program`, `client_area_delete_training_program` | Academy section (open / folders) |
| `academy/programs/<id>/lessons/add/` | `client_area_add_lesson` | GET: form for the modal; POST: lessons table, or the form with errors |
| `academy/lessons/<id>/availability/` | `client_area_set_lesson_availability` | Lessons table; 422 toast on invalid data |
| `academy/lessons/<id>/delete/` | `client_area_delete_lesson` | Lessons table |
| `academy/templates/add/` · `copy/` | `client_area_add_academy_template`, `client_area_copy_academy` | Academy section (the new program open / folders); 422 toast when the template is already in the client's academy |
| `program/activate/` · `program/deactivate/` | `client_area_activate_program`, `client_area_deactivate_program` | Tools partial; invalid period re-renders `#caProgressSection` |
| `access-requests/` | `client_area_access_requests` | Full pending list partial for the home "Ver todas" modal |
| `access-requests/<id>/accept/` | `client_area_accept_access` | GET: accept form (`?scope=pane\|home\|modal`). POST: tools partial (pane) or home block + modal list (OOB); `showToast`. Invalid period: form re-rendered with 200 |
| `catalog/search/` | `client_area_catalog_search` | JSON search results |

### Shared form modal

- Academy elements are added from an **Añadir contenido**
  button that opens `#clientAreaFormModal` (`components/modals/client-area-modals.html`, included by
  `contacts.html` outside `#contactModal`, together with the catalog picker).
- `data-ca-open-form` opens it with `Modal.show()`, not `data-bs-toggle`, so `#contactModal` stays
  open. The form partial (`client-area-tool-form.html`) fills the body and sets the title with
  `hx-swap-oob`.
- On success the view swaps only the table partial and sends `showToast` + `clientAreaFormSaved`
  (closes the modal). Invalid forms are re-rendered inside the modal with **200** (`HX-Retarget`).
- Add modals are one column. `cotton/tool_add_button` takes the form `url` (the academy elements
  of the open program).
- **Form sections.** Fields carry the repo's section attrs (`data_section` /
  `data_section_label`, as in `components/form-model.html`). `client-area-tool-form.html` prints
  the section title when it changes, and `cotton/form_field` hides the field label inside a
  section (the title labels it).

### Pane sections

- **Confirmations** — every `hx-confirm` inside `.client-area-tools` opens the global
  `#globalConfirmModal` (`openGlobalConfirmModal`, `static/js/global_confirm.js`) instead of the
  browser dialog: an `htmx:confirm` listener in `client_area_tools.js` issues the request on confirm.
- **Access** — access code with copy, accept request (start date and duration, see above),
  activate/deactivate access, WhatsApp link,
  App Store / Play Store badges (placeholders).
- **Evolución / Fotos** — horizontal scroll, edited inline (see *Evolución / Fotos tables*);
  Evolución also has its chart with a Desde / Hasta range.
  Deleting any row (client or advisor source) only sets `hidden_by_advisor`: the row leaves the web
  pane, the Fam Fit API still returns it.
- **Productos nutricionales** — Productos and Explicación (the `observations` field, widest
  column, `.ca-col-wide`), edited inline like Evolución (see
  *Evolución / Fotos tables*). Delete removes the row. The API reads products live (no cache).
- **Programa** — `client-area-program-table.html` (`#caProgramTable`, swapped `outerHTML`):
  Fecha, Alimentación, Deporte, Otros and a row delete (`hx-confirm`). Rows come from
  `services.pane.build_program_rows` (`ProgramCell` per column).
  - A filled cell (`client-area-program-cell.html`) shows the board item preview
    (`BoardItem.get_preview_url(allow_network=False)`, i.e. `mosaic_preview`, image or YouTube
    thumbnail) or a PDF icon, linked to the file; below it the name, truncated with an ellipsis,
    and `components/tooltip-view-more.html` with the full name.
  - An empty cell shows a dashed **+** button. Both open a dropdown
    (`client-area-program-cell-menu.html`): **Subir desde PC** (hidden file input, posted on
    `change`), **Desde board** (catalog picker opened in the column's folder via
    `data-ca-picker-folder`; the user can go back to the root) and, when filled, **Quitar**.
  - Each cell is one form: the picker writes its hidden input (`data-ca-picker-inputs`) and, with
    `data-ca-picker-submit`, `client_area_tools.js` submits it right away.
  - **Nuevo programa** below the table adds an empty row. There is no modal for program files.
- **Academia** — No/Sí toggle saved on change. Closed: one folder per programa formativo (name and
  element count; a template program shows a collection icon), a "Nuevo programa formativo" field
  and the **Plantillas** collapse ("Añadir desde plantilla" with the Videoteca templates not yet in
  this client's academy, "Copiar de otro cliente" with `hx-confirm`). Open: back button, inline
  rename, delete (`hx-confirm`), the elements table and **Añadir contenido**. Template elements show
  their content's title or text with a collection icon; their availability and delete only apply to
  this client.
  **Añadir contenido** opens `ClientLessonForm`, one column, in sections:

  | Section | Fields |
  |---|---|
  | Disponibilidad | `widgets.AvailabilityWidget`: "Siempre" checkbox with the "Día" input to its right (posted as `unlock_day_always` / `unlock_day`). Checking Siempre disables the day (`client_area_tools.js`); `AvailabilityField` requires a day ≥ 1 unless Siempre |
  | Contenido | `youtube_url`, validated with `extract_youtube_video_id`. Videos are YouTube links only: there is no video upload |
  | Texto | `text` |
  | Adjuntar archivo (PDF, imagen) | `attachment_source`: Subir archivo (`attachment_file`) / Desde board (`attachment_item`, PDF or image) |

  Fields with `data-ca-when="<source>=<value>"` are shown only for the checked option; `clean()`
  drops the inactive one and requires some content. `add_lessons` creates one element with the
  link, the text and the attachment. Each row has the same availability widget, saved on change
  (a checked Siempre or a typed day), and an `hx-confirm` delete.
- **Progreso** — `ProgramPeriodForm` (start date, duration; the end date is computed live by
  `client_area_tools.js` and never posted). Draft: **Activar**. Active: only **Desactivar**; the
  start date and duration are read-only.
### Home requests block

`components/card_client_access_requests.html` (`#client-access-requests-section`, included by
`main/home.html` when the user has the client area) shows the latest three pending
`ClientAccessRequest` rows as `<c-access-request-row>` cotton components: avatar, contact name,
what they ask for (access, or continuing the program with the order number), age ("Hace 2
horas"), a WhatsApp button and **Admitir**.

- **Ver todas** opens `#accessRequestsModal` (`components/modals/modal-access-requests.html`,
  extends `base-modal.html`). Its body loads `client_area_access_requests` with HTMX on every
  `show.bs.modal`, so the list is always fresh; there is no standalone page.
- **Admitir**, from the block or the modal, opens the accept form under the row (see *Accept a
  request*). Confirming posts to `client_area_accept_access`, which starts the program and returns
  the block (swapped `outerHTML`) plus the modal list with `hx-swap-oob`, and a `showToast` trigger.
  A request that is no longer pending returns a 422 toast.
- Both views require `user_has_client_area` and only see requests of the advisor's own contacts.

## Migrations

| Migration | Change |
|---|---|
| `0005_lesson_unlock_day_always` | `unlock_day` defaults to `0` on `ClientLesson` and `AcademyPlanItem`; lessons of assignments with `academy_unlock_mode="all"` get `unlock_day=0` (historical models) |
| `0006_remove_academy_unlock_mode_and_folders` | Drops `ClientProgramAssignment.academy_unlock_mode` and the `ClientProgramFolder` model |
| `0007_remove_clientproduct_board_item` | Drops `ClientProduct.board_item` |
| `0008_remove_clientprogramfile_file` | Drops `ClientProgramFile.file`: uploads are board items |
| `0009_trainingprogram` | Creates `TrainingProgram`; adds nullable `ClientLesson.program` and `attachment_item` on `ClientLesson` / `AcademyPlanItem` |
| `0010_default_training_programs` | Data (historical models): each assignment with lessons gets one "Programa formativo" (renamable, `source_plan` copied from the assignment) holding them |
| `0011_lesson_board_content_only` | `ClientLesson.program` becomes required; drops `ClientLesson.assignment`, `video_url`, `video_file`, `attachment`, the same content fields of `AcademyPlanItem`, and `ClientProgramAssignment.source_plan` |
| `0012_clientprogramentry` | Creates `ClientProgramEntry`; adds nullable `ClientProgramFile.entry` |
| `0013_program_files_to_entries` | Data (historical models): drops files without a board item; groups the rest into one row per (assignment, date), a repeated column opening another row |
| `0014_program_file_cell` | Drops `ClientProgramFile.assignment` / `assigned_on`; `entry` and `board_item` (`CASCADE`) become required; unique (`entry`, `slot`) |
| `0015_records_by_date_and_renewals` | Adds `ClientProgramAssignment.unlocked_through_day`. Data (historical models): merges duplicate measurements / photos of a client and date into the newest row, with the latest non-empty value of each field / slot (hidden only if every duplicate was); for clients with several programs, the latest takes the grid rows, products and academy it lacks from the newest older program that has them, and `unlocked_through_day` from the older periods. Then unique (`client_profile`, `recorded_on`) on both models. Photo files of the deleted duplicates that the merged row does not keep are deleted from storage |
| `0016_clientprofile_time_zone` | Adds `ClientProfile.time_zone` |
| `0017_client_body_composition` | Adds `ClientProfile.sex` / `height_cm` / `neck_cm` / `activity_level` and `ClientMeasurement.body_fat_pct` / `muscle_mass_kg`. Data: a numeric `bioimpedance.body_fat_pct` (2–75) / `muscle_mass_kg` (10–150) is copied to its field |
| `0018_remove_clientprofile_neck_cm` | Drops `ClientProfile.neck_cm` (body fat % is no longer calculated) |
| `0019_academy_templates` | Adds `TrainingProgram.template_folder`, `ClientLesson.template_item` / `hidden_by_advisor`; `ClientLesson.unlock_day` becomes nullable (needs `boards` `0013`) |
| `0020_academy_plans_to_videoteca` | Data (historical models), see below |
| `0021_remove_academy_plans` | Drops `ClientLesson.source_item`, `TrainingProgram.source_plan`, `AcademyPlanItem` and `AcademyPlan`; adds the template unique constraints |

`0020` turns the plantillas into Videoteca templates:

1. The existing Videoteca subfolders held the pane's per-client uploads, not templates: they move to
   Otros (the catalog folder, or the advisor's shadow folder of it, created if missing) with their items.
2. Each `AcademyPlan` becomes a folder named like it, dated with the plan's `updated_at`: in the
   catalog Videoteca for `USER_ROOT`, otherwise in the advisor's own Videoteca (board created if
   missing). Each `AcademyPlanItem` becomes an academy content with its `unlock_day` and `order`: a
   YouTube item gives the link, a text item adds its text to the plan text, a PDF / image / uploaded
   video item becomes the attachment when there was none. Files are shared by path, not copied.
3. Each program with `source_plan` points at its folder; a second copy of the same plan for the same
   client stays an own program. Its lessons from the plan become template elements that only keep an
   availability different from the template's; plan elements the client no longer had are added hidden.
   Own elements are untouched.

It does nothing without the catalog. Reverse: template elements become own elements of their academy
content (hidden ones are deleted); the plans are not rebuilt. `AcademyPlanItem` rows saved from
"all"-mode assignments kept their previous day (`0005`). Own lesson content
in the fields dropped by `0011` (video URL, video file, attachment) is not converted to board items.

## Configuration and Dependencies

App dependencies: `communication`, `boards`, `users`, `user_levels`, `pricing`. The add-on, its
per-level prices and Stripe checkout live in `pricing` (`Addon` code `client_area`, seeded by
`pricing` migration `0003`). Media goes through the global storage backend.

| Service | Use |
|---|---|
| Celery beat | `client_area.tasks.expire_client_programs_task` hourly at :15 (each client's day ends at their midnight) |
| Celery | `client_area.tasks.pause_lapsed_client_programs_task` (add-on lapse) |
| Redis | Catalog search reuses the boards search index |

No Sentry integration of its own.
