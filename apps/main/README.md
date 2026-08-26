# main

## Description

The authenticated home of the platform: dashboard, team management, incentive programs, the
distributor route, monthly acquisition stats, and the notification centre. It is the app users land
on after login and the one that aggregates data owned by the other domain apps.

Relationship to the core apps:

- **`users.User`** — every model here is scoped to a user, and the team views traverse the
  `sponsor` tree directly.
- **`user_levels`** — incentive CRUD goes through `check_action_allowed`, listings through
  `get_model_visible_queryset`, and downgrade warnings through `collect_downgrade_blocks`.
- **`core`** — constants, Quill payload helpers, file utilities, and the Redis-backed notification
  feed.

`main` reads from `challenge` (task progress on the dashboard), `communication` (scheduled tasks and
contacts), and `training` (team training stats), which makes it the app most exposed to N+1 risk;
the helpers in `utils.py` exist to keep those aggregations to a bounded number of queries.

## Models and Data

| Model | Purpose |
|---|---|
| `Notification` | Persistent per-user notifications (FK → `users.User`) |
| `TypeIncentive` | Ordered catalogue of incentive categories, admin-managed |
| `Incentive` | Incentive program: dates, location, Quill description, background image (FK → `users.User`, FK → `TypeIncentive`) |
| `IncentiveFile` | Attachments; max 3 enforced in `save_incentive` |
| `UserFavoriteIncentive` | Favourites join table |
| `MonthlyAcquisitionStats` | Monthly goals and cumulative counters per user |
| `RouteStep` | Leader-defined onboarding step template |
| `RouteStepProgress` | Per-distributor completion; two FKs to `users.User` (`distributor`, `tracker`) |
| `GeneralData` | Singleton row holding site-wide editable data |

`challenge.Task` has an optional FK to `Incentive`, which is how incentive-linked monthly tasks are
represented.

### Services (`services/`)

| Module | Key functions |
|---|---|
| `notifications.py` | `notify_incentive_creation` — personal notification, downline push, and leader copy-offer, wrapped so a failure never rolls back the incentive save |
| `incentives.py` | `copy_incentive_with_tasks`, `create_or_update_incentive_task`, `get_incentive_month_tasks`, `compute_incentive_type_order` |
| `route.py` | `resolve_route_owner`, `serialize_route_step`, `get_route_progress_ratio`, `attach_route_progress_to_children`, `build_distributor_route_payload`, `complete_route_step_for_distributor`, `save_leader_route_step`, `verify_user_access`, `validate_invitation_action` |

All three are re-exported from `services/__init__.py`.

### Utilities (`utils.py`)

| Function | Purpose |
|---|---|
| `get_first_leader_user()` | Resolves `FIRST_LEADER_PRO` by unique username |
| `build_scheduled_task_ranges(user, local_now, tz)` | Today / past / week / month `ScheduledTask` querysets |
| `build_month_calendar(...)` | Monthly calendar structure for the dashboard |
| `build_incentive_context(user, today, local_now)` | Full incentive context, free of N+1 |
| `build_downgrade_alerts(user)` | Downgrade alerts for the dashboard |
| `get_descendants_tree_optimized(user, max_depth)` | BFS descendant tree in one bulk query |
| `get_all_descendants_ids_with_generation(user, max_depth)` | BFS ID walk with generation numbers |
| `get_inactive_users_optimized(user, days)` | Inactive descendants; Redis cache, 5 min |
| `get_user_training_data_cached(user_id)` | Training stats; Redis cache, 10 min |
| `get_user_answers_cached(user_id)` | Answered training fields; Redis cache, 10 min |
| `invalidate_user_cache` / `invalidate_ancestors_cache` | Cache invalidation, cascading up the sponsor chain |
| `get_direct_children_with_data(user, generation)` | Children plus grandchild counts in two queries |
| `get_route_step(user)` | Route steps; copies from the nearest leader for plain leaders |

### Other modules

`birthdays.py` (birthday detection with Redis caching), `scheduled_task_reminders.py`, and
`tasks.py` — Celery tasks for FCM push delivery, birthday notices, and scheduled-task reminders.

## Views and Frontend Integration

**This app uses HTMX**: partially on the dashboard and extensively in the My Team section, where it
replaced the previous monolithic `my-team.js`.

URL prefix: **`/main/`**

### HTMX endpoints

| Endpoint | Name | Returns |
|---|---|---|
| `home/` (POST) | `home` | `components/card-sh-tasks.html` after completing a scheduled task |
| `set-monthly-goals/`, `save-monthly-stats/` | `set_monthly_goals`, `save_monthly_stats` | `components/monthly-stats.html` when `request.htmx` |
| `load-incentive-form/` | `load_incentive_form` | `components/partials/incentive-form-fields.html` |
| `my-team/` (POST) | `my_team` | Re-rendered invitation tree after sending an invite |
| `load-user-children/` | `load_user_children` | Lazy-loaded tree branch |
| `load-user-training-data/` | `load_user_training_data` | Training stats modal fragment |
| `load-user-answers/` | `load_user_answers` | Answered-fields modal fragment |
| `delete-pending-invitation/`, `resend-invitation/` | `delete_pending_invitation`, `resend_invitation` | Updated invitation row / actions cell |

Participating templates: `home.html` with `modal-confirm-complete.html`, `modal-add-new.html`, and
`base-modal.html`; `modal-incentive.html` driven by the global `static/js/htmx_modal_form.js`; and in
My Team, `modal-new-user.html`, `modal-delete-invitation.html`, `modal-resend-invitation.html`,
`invited-users-tree-lazy.html`, `invited-user-actions-cell.html`. Modals carry `data-close-modal`.

### HTML and JSON endpoints

| URL | Name | Description |
|---|---|---|
| `home/` | `home` | Dashboard: scheduled tasks, incentives, calendar, challenges |
| `my-team/` | `my_team` | Team tree, invitations, route steps |
| `personal-info/` | `personal_info` | Profile form |
| `save-incentive/` · `delete-incentive/` | `save_incentive`, `delete_incentive` | Incentive CRUD with attachments |
| `save-type-incentive/` | `save_type_incentive` | Category management, restricted to `USER_ROOT` |
| `save-favorite-incentive/` | `save_favorite_incentive` | Toggle favourite (JSON) |
| `create-incentive-task/` · `get-incentive-month-tasks/` | `create_incentive_task`, `get_incentive_month_tasks` | Monthly incentive tasks (JSON) |
| `copy/<id>/` | `copy_incentive` | Copies a visible incentive into the user's account |
| `register-push-subscription/` | `register_push_subscription` | Stores the FCM token (JSON). `@login_required` + `@require_POST`; **CSRF protection is active** |
| `set-notifications-activated/` | `set_notifications_activated` | Toggles notification opt-in |
| `notifications/` · `notification-redirect/` | `all_notifications`, `notification_redirect` | Notification centre and mark-read redirect |
| `save-route-step/` · `delete-route-step/` | `save_route_step`, `delete_route_step` | Leader route step CRUD (JSON or redirect depending on the AJAX header) |
| `load-distributor-route/` · `complete-distributor-route-step/` | `load_distributor_route`, `complete_distributor_route_step` | Distributor route payload and completion (JSON) |

Below-the-fold dashboard libraries (Leaflet, the geocoder, ApexCharts) are deferred; jQuery and
Bootstrap are self-hosted and loaded at the end of `<body>`.

### Access logic

- Every view requires authentication, enforced by `LoginRequiredMiddleware`.
- `save_type_incentive` is restricted to `USER_ROOT`.
- Incentive CRUD is validated with `check_action_allowed(user, INCENTIVE_MODEL_KEY, …)`.
- Route step writes require `is_any_leader()`.
- Team data endpoints call `verify_user_access`, which walks the sponsor chain up to depth 100.
- Only the direct sponsor may delete or resend a pending invitation.

## Configuration and Dependencies

| Setting | Purpose |
|---|---|
| `FIREBASE_CREDENTIALS_JSON`, `FIREBASE_WEB_*`, `FIREBASE_WEB_VAPID_KEY` | Push subscription registration and FCM delivery from `tasks.py` |
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Team, training, birthday, and inactivity caches |
| `R2_*` / `STORAGES` | Incentive background images and attachments |
| Email (SMTP) settings | Invitation and reminder emails |
| `USER_ROOT`, `FIRST_LEADER_PRO` (from `core.const`) | Bootstrap identities for admin-only actions |

External services: Redis, Celery (`tasks.py` for FCM push, birthdays, scheduled reminders), Firebase
Cloud Messaging, and the Leaflet / ApexCharts CDNs on the dashboard. **No direct Sentry integration**
— exceptions propagate to the global handler.

App dependencies: `challenge` (`Task`, `UserTaskProgress`, `get_progress_challenge_user`),
`communication` (`ScheduledTask`, `Contact`, `ActivityContact`), `core`, `training` (`UserProgress`),
`user_levels`, `users`.
