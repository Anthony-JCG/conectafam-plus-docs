# client_area

Advisor-side **client area**: nutrition/sport programs, access codes, measurements, academy
plans, and (later) the native client API. Consumers are `ClientProfile` rows linked to a
`communication.Contact`, not `users.User` nodes in the sponsor tree.

Relationship to the core apps:

- **`user_levels`** — `CLIENT_AREA_MODEL_KEY` + `ACCESS_ACTION_KEY`. Leader and Leader Pro are
  allowed. Basic/Pro are denied here; an add-on bypass is added in a later branch.
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
| `services/programs.py` | End date and active-window checks. |

No views yet. URLConf is empty; HTMX panes and `/api/client/` come in later branches.

## Configuration and Dependencies

App dependencies: `communication`, `boards`, `users`, `user_levels`. Media via the global storage
backend. No Stripe, Sentry, Redis, or Celery usage in this app yet.
