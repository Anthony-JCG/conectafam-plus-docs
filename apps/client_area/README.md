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
- **`users.User`** — the advisor owns `AcademyPlan`. The client is never this user.

## Models and Data

| Model | Relationships and fields |
|---|---|
| `ClientProfile` | OneToOne → `communication.Contact`. Unique `access_code`, `access_status` (`none` / `pending` / `active` / `deactivated`). |
| `ClientProgramAssignment` | FK → `ClientProfile`. `start_date`, `duration_days`, `deactivated_at`, `academy_enabled`. The end date is derived (`start_date + duration_days`), never stored. |
| `ClientProgramFile` | FK → assignment; slot `nutrition` / `sport` / `other`; FK → `BoardItem` (the file; uploads become board items). |
| `ClientProduct` | FK → assignment; `recorded_on`, `products`, `observations`. Plain text, no board item. |
| `TrainingProgram` | Programa formativo: FK → assignment (`training_programs`); optional FK → `AcademyPlan` (`source_plan`); `name`, `order`. One Academia folder. |
| `ClientLesson` | FK → `TrainingProgram` (`lessons`); one academy element: `board_item` (the content: uploaded video, YouTube or any picked item), `text`, `attachment_item` (PDF / image board item), `unlock_day`, `order`; optional FK → `AcademyPlanItem` (`source_item`). |
| `AcademyPlan` | FK → `users.User` (advisor). Plantilla of one programa formativo: its name and `AcademyPlanItem` rows. |
| `AcademyPlanItem` | FK → `AcademyPlan`; `board_item`, `text`, `attachment_item`, `unlock_day`, `order`, like `ClientLesson`. |
| `ClientMeasurement` | FK → profile; body metrics and `bioimpedance`; `source=client\|advisor`; `hidden_by_advisor`. |
| `ClientProgressPhoto` | FK → profile; front/back/side; `source`; `hidden_by_advisor`. |
| `ClientAccessRequest` | FK → profile; `kind` first access / continuity; optional `order_number` / `purchase_date`. |

Everything except `AcademyPlan` / `AcademyPlanItem` hangs from `ClientProfile` with `CASCADE`, so
deleting the contact deletes its whole client area (see the `communication` README). FKs to
`BoardItem` are `SET_NULL`: deleting a board item leaves the row without it.

### Program lifecycle

| State | Condition | Client access |
|---|---|---|
| Draft | `start_date` is `null` | Unchanged |
| Active | `start_date <= today <= start_date + duration_days`, `deactivated_at` null | `active` (granted on activation) |
| Ended | `deactivated_at` set (advisor, daily expiry or add-on lapse) | `none` ("Sin acceso") |

- **Activate** (`activate_program`) stores the start date and duration, accepts pending access
  requests (`access_actions.grant_access_for_program`) or activates the profile, and writes an
  `ActivityContact` note.
- **Duration lock.** Once the program has a start date, `duration_days` is fixed:
  `ProgramPeriodForm(assignment=...)` renders it disabled (a posted value is ignored) and
  `activate_program` raises `ValueError` for a different value. The start date stays editable and
  the end date moves with it.
- **Deactivate / expire.** `deactivate_program` and the daily `expire_due_programs` set
  `deactivated_at` and call `clear_access_on_program_end` (`access_status=none`); the next Fam Fit
  login creates a new `first_access` request.
- Tools always edit the **working assignment** (`get_or_create_working_assignment`): the latest
  non-deactivated one, or a new draft. An ended assignment keeps its content, but the next program
  starts from a new draft.

### Academia: programas formativos

Academia is a set of **programas formativos** (`TrainingProgram`), shown as folders; opening one
lists its elements (`ClientLesson`) and manages them. Programs can be created, renamed and deleted
(deleting removes its elements; their board items stay in the board). The No/Sí
`academy_enabled` toggle stays on the assignment and covers every program.

Programs belong to the **client's assignment**, not to the advisor:

- Availability is relative to each client's program day, like the lessons already were.
- Reuse goes through **Plantillas**: `AcademyPlan` stores one programa formativo.
  "Guardar como plantilla" (`save_program_as_plan`) saves the open program under its name and
  replaces the items of the advisor's plan with that name; "Añadir desde plantilla"
  (`add_program_from_plan`) adds a new program with a copy of the plan's elements
  (`source_plan` / `source_item`) and enables the academy. "Copiar de otro cliente"
  (`copy_academy_from_client`) replaces every program of the client with a copy of the other
  client's programs.
- The reusable content itself is the board: `Videoteca / <program name>` holds the uploads of
  every client whose program has that name.

### Academy availability

Each `ClientLesson` has its own availability in `unlock_day` (`UNLOCK_DAY_ALWAYS = 0`):

| `unlock_day` | Pane label | Unlocked when |
|---|---|---|
| `0` | Siempre | Always, while the academy is enabled |
| `N >= 1` | Día N | `program_day >= N` |

`todays_lesson` is the first lesson (programs and lessons in order) whose `unlock_day` equals the
current program day; "Siempre" lessons never are. The assignment only keeps the No/Sí `academy_enabled` toggle; there is no academy-wide
mode. Plans and copy-from-client keep each element's `unlock_day`.

### Services

| Module | Responsibility |
|---|---|
| `services/access.py` | Unique access-code allocation |
| `services/access_actions.py` | Accept requests, activate/deactivate access, grant on program start, clear on program end, continuity WhatsApp texts |
| `services/entitlement.py` | `user_has_client_area(user)`: capability **or** `user_has_addon(user, CLIENT_AREA_ADDON_CODE)` |
| `services/profiles.py` | `get_or_create_client_profile` |
| `services/programs.py` | Working assignment, `activate_program` / `deactivate_program`, end date, program day, progress, contact status and list filter |
| `services/content.py` | Measurements, photos, `assign_program_file` / `upload_program_file`, `add_product(profile, data)`, `hide_by_advisor` |
| `services/academy.py` | `set_academy_enabled`, `create_training_program`, `add_lessons(program, ...)`, `set_lesson_unlock_day`, `save_program_as_plan`, `add_program_from_plan`, `copy_academy_from_client`, `lesson_is_unlocked`, `todays_lesson` |
| `services/catalog.py` | Advisor's client-area boards and catalog search |
| `services/pane.py` | Tools pane context, `build_catalog_context`, WhatsApp URLs |
| `services/inbox.py` | `pending_access_requests_for_advisor` (newest first, with contact, WhatsApp URL and age) for the home block; `HOME_ACCESS_REQUESTS_LIMIT = 3` |
| `services/expiry.py` | Daily expiry and `pause_programs_without_entitlement` |

## Catalog board

The advisor works with **one** board, "Área de clientes" (`CLIENT_AREA_OWN_BOARD_TITLE`): their
private client-area board, whose views merge the FAM TEAM system catalog read-only. Storage,
permissions and shadow folders are described in the `apps/boards` README ("Client-area boards").

| Part | Owner | Allowed item types | Advisor can |
|---|---|---|---|
| System catalog (Nutrición, Deporte, Videoteca, Otros) | `USER_ROOT` | PDF, image; Videoteca also uploaded video and YouTube | View and pick; add own items and subfolders inside its folders (shadow folders) |
| Own content | Advisor | Folders, text, image, PDF, uploaded video, YouTube | Full CRUD inside the catalog folders; nothing at the board root |

- `services/pane.build_catalog_context` returns `catalog_board` (the own board).
  `.client-area-tools` carries its id and `board_mosaic_data` URL; the picker in
  `client_area_tools.js` opens that merged mosaic, with a back button inside folders.
  Read-only tiles are selectable and the selection survives folder navigation and search.
- `search_client_area_catalog` filters the boards Redis index to the same two boards and renders
  results with `textContent`.
- `CatalogItemFormMixin` scopes its `catalog_fields` to
  `get_client_area_catalog_boards_queryset(advisor)`, so no item from another board is accepted.
- The picker field widget is `widgets.CatalogPickerInput(multiple=...)`: an "Añadir desde board"
  button plus the hidden ids that `client_area_tools.js` writes, keyed by the field name (several
  pickers per form).

| Tool | Picker |
|---|---|
| Program files (`ClientProgramBoardFileForm.board_item`, "Añadir desde board" button) | One item |
| Academy content (`ClientLessonForm.board_items`) | Several items, one element each |
| Academy attachment (`ClientLessonForm.attachment_item`) | One PDF or image |
| Nutritional products | None |

### Board storage

Content uploaded from the pane (not picked from the board) is stored as a board item first, and
the program file or lesson references it: the board item is the source of truth.
`boards.services.client_area_uploads` resolves the folder: for an advisor, their shadow folder of
the catalog root folder (`ensure_shadow_folder`); for `USER_ROOT`, the catalog folder itself.

| Upload | Board folder |
|---|---|
| Programa, Tipo Alimentación (`nutrition`) | Nutrición |
| Programa, Tipo Deporte (`sport`) | Deporte |
| Programa, Tipo Otros (`other`) | Otros |
| Academia: video, YouTube link, attachment | Videoteca / `<program name>` (subfolder created on first upload) |

`const.PROGRAM_SLOT_FOLDERS` maps slots to folders. The Videoteca subfolder is resolved by name on
each upload: renaming a program does not rename the folder (it may be shared with other clients'
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
| `forms/<kind>/` | `client_area_tool_form` | Form partial for the shared modal (`views.TOOL_FORMS`) |
| `access/accept/` · `activate/` · `deactivate/` | `client_area_accept_access`, `client_area_activate_access`, `client_area_deactivate_access` | Tools partial |
| `measurements/add/` · `photos/add/` | `client_area_add_measurement`, `client_area_add_photo` | Table partial, or the form with errors |
| `measurements/hide/` · `photos/hide/` | `client_area_hide_measurement`, `client_area_hide_photo` | Table partial |
| `program/assign/` | `client_area_assign_program` | Upload (stored in the board): table partial, or the form with errors |
| `program/assign-from-board/` | `client_area_assign_program_from_board` | Picked board item: table partial, or the form with errors |
| `products/add/` | `client_area_add_product` | Table partial, or the form with errors |
| `products/<id>/edit/` | `client_area_edit_product` | GET: filled form; POST: table partial, or the form with errors |
| `products/<id>/delete/` | `client_area_delete_product` | Table partial |
| `academy/` (GET) | `client_area_academy` | Academy section with the program folders |
| `academy/toggle/` | `client_area_toggle_academy` | Academy section (keeps the program posted as `program_id` open) |
| `academy/programs/add/` | `client_area_add_training_program` | Academy section with the new program open; 422 toast on invalid name |
| `academy/programs/<id>/` (GET) | `client_area_training_program` | Academy section with the program open |
| `academy/programs/<id>/rename/` · `delete/` | `client_area_rename_training_program`, `client_area_delete_training_program` | Academy section (open / folders) |
| `academy/programs/<id>/save-template/` | `client_area_save_training_program_template` | Academy section, program open |
| `academy/programs/<id>/lessons/add/` | `client_area_add_lesson` | GET: form for the modal; POST: lessons table, or the form with errors |
| `academy/lessons/<id>/availability/` | `client_area_set_lesson_availability` | Lessons table; 422 toast on invalid data |
| `academy/lessons/<id>/delete/` | `client_area_delete_lesson` | Lessons table |
| `academy/plans/reuse/` · `copy/` | `client_area_reuse_academy_plan`, `client_area_copy_academy` | Academy section (the new program open / folders) |
| `program/activate/` · `program/deactivate/` | `client_area_activate_program`, `client_area_deactivate_program` | Tools partial; invalid period re-renders `#caProgressSection` |
| `access-requests/` | `client_area_access_requests` | Full pending list partial for the home "Ver todas" modal |
| `access-requests/accept/` | `client_area_accept_access_home` | Home block (main swap) + modal list (OOB); `showToast` |
| `catalog/search/` | `client_area_catalog_search` | JSON search results |

### Shared form modal

- Rows of measurements, photos, program files, products and academy are added from an **Añadir**
  button that opens `#clientAreaFormModal` (`components/modals/client-area-modals.html`, included by
  `contacts.html` outside `#contactModal`, together with the catalog picker).
- `data-ca-open-form` opens it with `Modal.show()`, not `data-bs-toggle`, so `#contactModal` stays
  open. The form partial (`client-area-tool-form.html`) fills the body and sets the title with
  `hx-swap-oob`.
- On success the view swaps only the table partial and sends `showToast` + `clientAreaFormSaved`
  (closes the modal). Invalid forms are re-rendered inside the modal with **200** (`HX-Retarget`).
- Add modals are one column (`ToolForm.field_class = "col-12"`); only Evolución (measurements)
  keeps two (`col-12 col-sm-6`). `cotton/tool_add_button` takes an optional `url` for forms of a
  nested object (academy elements of a program).
- **Form sections.** Fields carry the repo's section attrs (`data_section` /
  `data_section_label`, as in `components/form-model.html`). `client-area-tool-form.html` prints
  the section title when it changes, and `cotton/form_field` hides the field label inside a
  section (the title labels it).

### Pane sections

- **Access** — access code with copy, accept request, activate/deactivate access, WhatsApp link,
  App Store / Play Store badges (placeholders).
- **Evolución / Fotos** — horizontal scroll. Deleting any row (client or advisor source) only sets
  `hidden_by_advisor`: the row leaves the web pane, the Fam Fit API still returns it.
- **Productos nutricionales** — `ClientProductForm` (date, products, observations; no catalog
  picker). Clicking a row opens the same modal filled in (`data-ca-open-form` + `hx-get`); the delete
  cell is `data-ca-row-action`, ignored by the row click, with an `hx-confirm`
  `btn-outline-danger` button. Delete removes the row. The API reads products live (no cache).
- **Programa** — **Asignar programa** (`ClientProgramFileForm`: Tipo, Fecha, PDF / image upload
  stored in the board) and, next to it, **Añadir desde board** (`ClientProgramBoardFileForm`: Tipo,
  Fecha, one picked item). The table shows the board item titles.
- **Academia** — No/Sí toggle saved on change. Closed: one folder per programa formativo (name and
  element count), a "Nuevo programa formativo" field and the **Plantillas** collapse ("Añadir desde
  plantilla", "Copiar de otro cliente" with `hx-confirm`). Open: back button, inline rename,
  delete (`hx-confirm`), the elements table, **Añadir contenido** and **Guardar como plantilla**.
  **Añadir contenido** opens `ClientLessonForm`, one column, in sections:

  | Section | Fields |
  |---|---|
  | Disponibilidad | `widgets.AvailabilityWidget`: "Siempre" checkbox with the "Día" input to its right (posted as `unlock_day_always` / `unlock_day`). Checking Siempre disables the day (`client_area_tools.js`); `AvailabilityField` requires a day ≥ 1 unless Siempre |
  | Contenido | `widgets.SegmentedRadioSelect` `content_source`: Subir vídeo (`video_file`) / YouTube (`youtube_url`, validated with `extract_youtube_video_id`) / Desde board (`board_items`, several) |
  | Texto | `text` |
  | Adjuntar archivo (PDF, imagen) | `attachment_source`: Subir archivo (`attachment_file`) / Desde board (`attachment_item`, PDF or image) |

  Fields with `data-ca-when="<source>=<value>"` are shown only for the checked option; `clean()`
  drops the inactive ones and requires some content. `add_lessons` creates one element per content
  item (upload, YouTube or each picked item), each with the text and attachment; with text or an
  attachment only, a single element. Each row has the same availability widget, saved on change
  (a checked Siempre or a typed day), and an `hx-confirm` delete.
- **Progreso** — `ProgramPeriodForm` (start date, duration; the end date is computed live by
  `client_area_tools.js` and never posted). Draft: **Activar**. Active: **Guardar** and
  **Desactivar**, with the duration read-only.
### Home requests block

`components/card_client_access_requests.html` (`#client-access-requests-section`, included by
`main/home.html` when the user has the client area) shows the latest three pending
`ClientAccessRequest` rows as `<c-access-request-row>` cotton components: avatar, contact name,
what they ask for (access, or continuing the program with the order number), age ("Hace 2
horas"), a WhatsApp button and **Admitir**.

- **Ver todas** opens `#accessRequestsModal` (`components/modals/modal-access-requests.html`,
  extends `base-modal.html`). Its body loads `client_area_access_requests` with HTMX on every
  `show.bs.modal`, so the list is always fresh; there is no standalone page.
- **Admitir**, from the block or the modal, posts to `client_area_accept_access_home`, which accepts
  the request (`accept_access_request`) and returns the block (swapped `outerHTML`) plus the modal
  list with `hx-swap-oob`, and a `showToast` trigger. Errors return a 422 toast.
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

`AcademyPlanItem` rows saved from "all"-mode assignments keep their previous day. Own lesson content
in the fields dropped by `0011` (video URL, video file, attachment) is not converted to board items.

## Configuration and Dependencies

App dependencies: `communication`, `boards`, `users`, `user_levels`, `pricing`. The add-on, its
per-level prices and Stripe checkout live in `pricing` (`Addon` code `client_area`, seeded by
`pricing` migration `0003`). Media goes through the global storage backend.

| Service | Use |
|---|---|
| Celery beat | `client_area.tasks.expire_client_programs_task` daily at 05:15 |
| Celery | `client_area.tasks.pause_lapsed_client_programs_task` (add-on lapse) |
| Redis | Catalog search reuses the boards search index |

No Sentry integration of its own.
