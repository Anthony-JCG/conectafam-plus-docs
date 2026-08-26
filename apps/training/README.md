# training

## Description

Training and onboarding system. Content is organised in three levels — **category → section (course)
→ subsection (formation)** — and split into two modes: `first_steps`, the mandatory onboarding path,
and `my_resources`, the leader's own training library.

The app owns a hard gate on the rest of the platform: until a user completes the initial training,
`users.middle.InitialTrainingGateMiddleware` redirects every request to `/training/onboarding/`.
Completing it is also what activates the free trial handled by `user_levels`.

Relationship to the core apps:

- **`user_levels`** — content visibility, per-level gating (`visible_from` uses `LevelType` as
  choices, not a FK), creation permissions, and downgrade handling.
- **`core`** — constants (`FIRST_STEPS_TRAINING`, `MY_RESOURCES_TRAINING`), Quill payloads, Redis
  caching, notifications, and file utilities.
- **`users.User`** — owns categories, authored subsections, progress, and messages.

`first_steps` visibility has its own line-cut rule (`apply_first_steps_line_cut`,
`get_first_steps_top_sponsor`) layered on top of the standard sponsor traversal.

## Models and Data

| Model | Relationships |
|---|---|
| `CategoryTraining` | FK → `users.User`. Top level; `visible_from` restricts it by level |
| `Section` | FK → `CategoryTraining` — a course |
| `Subsection` | FK → `Section`; FK → `users.User` (nullable, author) — a formation |
| `CategoryTrainingAccess` | FK → `CategoryTraining`; FK → `users.User` — explicit grants for hidden categories |
| `SubsectionFile` | FK → `Subsection` — attachments |
| `InputFieldSubsection` | FK → `Subsection` — questions rendered inside a formation |
| `UserProgress` | FK → `users.User`; FK → `Subsection` — completion tracking |
| `UserProgressAnswer` | FK → `UserProgress`; FK → `InputFieldSubsection` — submitted answers |
| `TrainingMessages` | FK → `users.User` — start/end messages shown around a formation |
| `TrainingUserMessages` | FK → `users.User`; FK → `TrainingMessages` — per-user delivery state |

### Utilities

There is no `services.py`. Logic lives in:

| Module | Responsibility |
|---|---|
| `utils.py` | First-steps visibility (`apply_first_steps_line_cut`, `get_first_steps_top_sponsor`), progress aggregation (`build_first_steps_progress_data`), resolution of the effective first subsection, sponsor notification emails, start/end message handling |
| `forms.py` | Category, section, subsection, message, and first-formation forms |
| `signals.py` | Creates a default category when a `leader_pro` is created; invalidates progress and hidden-access caches. Registered from `apps.py` |

## Views and Frontend Integration

**This app does not use HTMX.** Its dynamic behaviour is fetch/AJAX returning `JsonResponse`, often
with pre-rendered HTML inside an `html` key.

> `templates/components/modal-confirm-complete.html` contains a conditional `hx-post` attribute, but
> every `include` of it (`initial-training.html`, `training-course-formations.html`) passes
> `no_reload="1"` without `hx_post`, so the HTMX branch is never emitted. It is dead markup.

URL prefix: **`/training/`**

| URL | View | Response |
|---|---|---|
| `mode/<training_mode>/` | `initial_training` | Category listing for the mode (HTML); POST marks progress and returns JSON under AJAX |
| `mode/<training_mode>/course/<section_id>/` | `training_course_formations` | Course detail with its formations (HTML) |
| `onboarding/` | `onboarding` | Blocking initial-training flow (HTML) |
| `global-search/` | `global_training_search` | Search across visible categories, courses, and formations (JSON) |
| `load_category_content/<id>/` | `load_category_content` | Lazy-loads a category's courses (JSON + HTML) |
| `load_section_content/<id>/` | `load_section_content` | Lazy-loads a course's formations (JSON + HTML) |
| `load_subsection_item/<id>/` | `load_subsection_item` | Refreshes a single formation (JSON + HTML) |
| `submit_subsection_answers/` | `submit_subsection_answers` | Stores answers and marks completion (JSON) |
| `upload_subsection_file/` · `delete_subsection_file/` | `upload_subsection_file`, `delete_subsection_file` | Attachment CRUD (JSON) |
| `save_category/` · `save_section/` · `save_subsection/` | `save_category`, `save_section`, `save_subsection` | Authoring CRUD for leaders (JSON) |
| `save_input_field/` · `delete_input_field/` | `save_input_field`, `delete_input_field` | Question CRUD (JSON) |
| `hidden_category_access/<id>/` · `save_hidden_category_access/` | `get_hidden_category_access`, `save_hidden_category_access` | Access management for hidden categories (JSON) |
| `save_first_formation/` | `save_first_formation` | Saves the leader's first custom formation (redirect) |
| `save-training-messages/` | `save_training_messages` | Start/end message configuration (redirect) |
| `delete_element/` | `delete_element` | Deletes an owned category, course, or formation (JSON) |
| `update_order/` | `update_order` | Drag-and-drop reordering (JSON) |

## Configuration and Dependencies

| Setting | Purpose |
|---|---|
| `FIRST_STEPS_TRAINING`, `MY_RESOURCES_TRAINING` (from `core.const`) | Mode identifiers used in URLs and queries |
| `FIRST_STEPS_LINE_CUT_USERNAME` (from `core.const`) | Anchor user for the first-steps visibility cut |
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Progress and hidden-access caches, invalidated by signals |
| `R2_*` / `STORAGES` | Formation attachments and images through the global media backend |
| Email (SMTP) settings | Sponsor notifications when a downline user completes training |

App dependencies: `core`, `users`, `user_levels`, `main` (notifications and descendant cache
invalidation).

**No direct Sentry, Celery, or Stripe integration.** The free trial that starts on training
completion is owned by `user_levels`; see [`apps/pricing/README.md`](../pricing/README.md) for how it
interacts with billing.
