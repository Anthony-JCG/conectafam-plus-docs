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
| `ClientProgramAssignment` | FK → `ClientProfile`; optional FK → `AcademyPlan`. Start date, duration, academy toggle, drip vs all. |
| `ClientProgramFolder` | FK → assignment + `boards.BoardFolder`. |
| `ClientProgramFile` | FK → assignment; slot nutrition/sport/other; optional `BoardItem` or file. |
| `ClientProduct` | FK → assignment; date, products, observations. |
| `ClientLesson` | FK → assignment; copy of plan item content + `unlock_day`. |
| `ClientMeasurement` | FK → profile; body metrics; `source=client\|advisor`. Advisor must not delete `source=client`. |
| `ClientProgressPhoto` | FK → profile; front/back/side. |
| `ClientAccessRequest` | FK → profile; first access or continuity. |

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

- Evolution and photo tables scroll horizontally (~4 columns visible). Advisors can add rows/photos and delete **advisor-sourced** rows only (`source=client` is protected).
- Home card **Solicitudes** (near scheduled tasks) lists pending `ClientAccessRequest` rows with Admitir / WhatsApp / Ver todas.
- Listing page: `client_area_access_requests`.
- `activate_program` / `deactivate_program` write `ActivityContact` notes (expiry job already notes automatic end).

