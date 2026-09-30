# client_area

Advisor-side **client area**: nutrition/sport programs, access codes, measurements, academy
plans, and (later) the native client API. Consumers are `ClientProfile` rows linked to a
`communication.Contact`, not `users.User` nodes in the sponsor tree.

Relationship to the core apps:

- **`user_levels`** — `CLIENT_AREA_MODEL_KEY` + `ACCESS_ACTION_KEY`. Leader and Leader Pro are
  allowed. Basic/Pro are denied there; `user_has_client_area` also accepts the purchased
  `client_area` add-on (`pricing.UserAddon`).
- **`communication`** — `ClientProfile.contact` is OneToOne to `Contact`. Program start/end notes
  will write `ActivityContact` rows.
- **`boards`** — catalog items and academy folders point at `BoardItem` / `BoardFolder`.
- **`users.User`** — advisor owns `AcademyPlan`. The client is never this user.

## Models and Data

| Model | Relationships |
|---|---|
| `ClientProfile` | OneToOne → `communication.Contact`. Unique `access_code`. Access status. No User FK (device tokens come with the API). |
| `AcademyPlan` | FK → `users.User` (advisor). Named reusable lesson set. |
| `AcademyPlanItem` | FK → `AcademyPlan`; optional FK → `boards.BoardItem`; `unlock_day`. |
| `ClientProgramAssignment` | FK → `ClientProfile`; optional FK → `AcademyPlan`. Start date + duration (end date derived, not stored), academy toggle, `academy_unlock_mode` (`all` = Siempre, `drip` = Por días; one mode for the whole academy). |
| `ClientProgramFolder` | FK → assignment + `boards.BoardFolder`. |
| `ClientProgramFile` | FK → assignment; slot nutrition/sport/other; optional `BoardItem` or file. |
| `ClientProduct` | FK → assignment; date, products, observations. |
| `ClientLesson` | FK → assignment; copy of plan item content + `unlock_day`. |
| `ClientMeasurement` | FK → profile; body metrics; `source=client\|advisor`; `hidden_by_advisor` hides the row on the web only. |
| `ClientProgressPhoto` | FK → profile; front/back/side; `hidden_by_advisor` (web only). |
| `ClientAccessRequest` | FK → profile; first access or continuity; optional `order_number` / `purchase_date`. |

### Services

| Module | Responsibility |
|---|---|
| `services/access.py` | Unique access-code allocation. |
| `services/entitlement.py` | `user_has_client_area(user)` — capability **or** `user_has_addon(user, CLIENT_AREA_ADDON_CODE)`. |
| `services/programs.py` | End date, active-window checks, contact status display, list filter. |

The contact-modal tab is in `communication`. Locked Basic/Pro users see
`RestrictedAccessAlert` `client_area_addon`, whose button posts to
`create_addon_checkout` with `client_area`. With entitlement, `#pane-cliente` HTMX-loads
`load_client_area_pane` (`/client-area/load-pane/`) with a section skeleton; full tools arrive in
later branches. Contact cards show program active/inactive status from `services/programs.py`
(not CRM `membership`). `/api/client/` is implemented in `apps/client_api` (Fam Fit native app).

## Configuration and Dependencies

App dependencies: `communication`, `boards`, `users`, `user_levels`, `pricing`. Media via the
global storage backend. The add-on catalog, its per-level prices, and Stripe checkout live in
`pricing` (`Addon` with code `client_area`, seeded by `pricing` migration `0003`).
Celery beat runs expire_client_programs_task daily; catalog search reuses boards Redis index.

## Catalog board (boards)

Shared FAM TEAM catalog lives as a `boards.Board` with `is_client_area=True`, seeded by
`python manage.py seed_client_area_board` (folders: Nutrición, Deporte, Videoteca, Otros).
Advisors with `user_has_client_area` can open it read-only and pick `BoardItem` /
`BoardFolder` references for programs. They cannot edit system content; personal files
belong on their own boards or `ClientProgramFile` uploads. See `apps/boards` README.

## Web tools polish (Rama 6)

- Evolution and photo tables scroll horizontally (~4 columns visible). Advisors can add rows/photos and delete any row (client or advisor source): deleting only sets `hidden_by_advisor`, so the row disappears from the web pane while the Fam Fit API (`/api/client/`) keeps returning it. There is no undo.
- Rows for evolution, photos, program files and nutritional products are added from an **Añadir** button that
  opens the shared `#clientAreaFormModal` (`components/modals/client-area-modals.html`, included by `contacts.html`
  outside `#contactModal` so it stacks correctly, together with the catalog picker). The button opens it with
  `Modal.show()` (`data-ca-open-form`), not `data-bs-toggle`, which would hide `#contactModal`. `client_area_tool_form`
  (`forms/<kind>/`) loads the form from `views.TOOL_FORMS`; on success the view swaps only that table partial
  (`components/partials/client-area-*-table.html`) and sends `showToast` + `clientAreaFormSaved` (closes the modal).
  Invalid forms are re-rendered inside the modal (`HX-Retarget`). The modal shell extends the global
  `base-modal.html` (`client-area-form-modal.html`); the form partial (`components/partials/client-area-tool-form.html`)
  fills its body and sets the title via `hx-swap-oob`. Cotton components: `form_field`, `tool_add_button`.
- **Academy** (`components/partials/client-area-academy.html`): the No/Sí toggle and **Contenido disponible**
  (`Siempre` = `all`, every lesson open; `Por días` = `drip`, a lesson opens on program day `unlock_day`) are saved
  on change (`client_area_toggle_academy`). Catalog folders are selectable cards, also saved on
  change. Only that section is re-rendered. **Añadir contenido** opens the shared form modal with `ClientLessonForm`
  (kind `lesson`) and on save swaps only the lessons table. Templates and copy-from-client live in the **Plantillas**
  collapse.
- **Progress** (`components/partials/client-area-progress.html`): the advisor picks the start date and the duration
  (`ProgramPeriodForm`). The end date is read-only: `client_area_tools.js` updates it live, and the server never
  receives it because it is always derived from start + duration (`program_end_date`). So there is no end-date
  column; the Fam Fit API keeps its fields and adds `start_date` to the `program` block. Before the program starts
  the button is **Activar**; afterwards it shows **Guardar** (updates start and duration) and **Desactivar**. An
  invalid form re-renders the section with its errors. Headings, inputs and buttons use the compact sizes of the rest
  of the pane.
- **Program ↔ app access**: `activate_program` calls `access_actions.grant_access_for_program`, which accepts any
  pending access request (first access or continuity) or otherwise activates the profile, so the client can log in
  to Fam Fit with `access_code` + `device_id`. `deactivate_program` and the daily expiry job both call
  `clear_access_on_program_end`, which puts access back to `none` ("Sin acceso"); the next login with the code
  creates a new `first_access` request for the advisor.
- Home card **Solicitudes** (near scheduled tasks) lists pending `ClientAccessRequest` rows with Admitir / WhatsApp / Ver todas.
- Listing page: `client_area_access_requests`.
- `activate_program` / `deactivate_program` write `ActivityContact` notes (expiry job already notes automatic end).

