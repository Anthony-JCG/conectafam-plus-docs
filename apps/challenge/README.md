# challenge

## Description

Challenges and their recurring daily/monthly tasks. Users create challenges, join those shared by
their upline leader, and record progress per task and date. Supports both leader-shared challenges
and purely personal task lists.

Relationship to the core apps:

- **`user_levels`** — visibility comes from `get_challenge_visible_queryset`, permissions from
  `check_action_allowed` and `can_delete_challenge`, and downgrade restrictions from
  `collect_downgrade_blocks`. Whether a challenge may be non-personal is a level decision, not one
  taken here.
- **`core`** — constants (`PERSONAL_CHALLENGE_NAME`, `MAX_CHALLENGES_PER_USER`), notification
  helpers (`notify_downline`, `send_personal_notification`), and day-scheduling utilities
  (`get_tasks_for_day`).
- **`users.User`** — owns challenges and all progress records.
- **`main`** — `Task` may belong to a `main.Incentive` instead of a `Challenge`.

## Models and Data

### `Challenge`

Created by a user; either personal (private) or shared with the downline. FK → `users.User`.

| Field | Notes |
|---|---|
| `challenge_collect_type` | `unique` — only one active per user; `set` — multiple allowed |
| `challenge_type` | `static` — resets on the 1st of the month; `dynamic` — starts from the join date |
| `is_personal` | Hides it from the downline; forced on for non-leader users |

### `Task`

Belongs to a `Challenge` **or** to a `main.Incentive` — mutually exclusive, validated in `clean()`.
The `day` field drives scheduling (`"1-31"`, `"1-15"`, …) and is parsed by `core.utils.task_days`.

### `UserChallengeProgress`

Tracks active participation. FK → `users.User`, FK → `Challenge`;
`unique_together = ("user", "challenge")`.

`get_daily_tasks()` returns today's tasks with completion state, resolving progress through a
**single bulk query** to avoid N+1 when rendering task cards.

### `UserTaskProgress`

Per user, per task, per date. `unique_together = ("user", "task", "date")`.

- Daily tasks: `date = today`.
- Monthly tasks: `date = first day of the month`, canonicalised by
  `services.get_or_update_task_progress`.

### `UserTaskOrder`

Custom per-user task ordering. FK → `users.User`, FK → `Task`. Reserved for future use.

### Services (`services.py`)

| Function | Description |
|---|---|
| `copy_challenge_with_tasks(user, source)` | Deep-copies a challenge and its tasks with `bulk_create`. The copy is always personal |
| `get_or_update_task_progress(user, task, date, *, mark_complete, progress_value)` | Gets or creates the progress row and applies the mutation, handling daily/monthly date canonicalisation |
| `deactivate_orphan_unique_progresses(user)` | Deactivates `unique`-type progress rows left without a valid active challenge |

`utils.get_progress_challenge_user` filters visible active progresses.

## Views and Frontend Integration

**This app does not use HTMX.** There are no `hx-*` attributes in its templates and no
`request.htmx` branches in its views. Interaction is a mix of standard form posts and one AJAX
endpoint that answers `JsonResponse` when the request carries
`X-Requested-With: XMLHttpRequest`.

URL prefix: **`/challenges/`**

| URL | View | Description |
|---|---|---|
| `""` | `challenges` | POST creates a challenge; GET redirects to `my_challenges#manage-challenges` |
| `edit/<id>/` | `edit_challenge` | Edit a challenge and its task list |
| `delete-challenge/` | `delete_challenge` | Delete a challenge or a task |
| `my-challenges/` | `my_challenges` | Unified view: join/leave, admin panel, personal tasks |
| `my-tasks/` | `my_tasks` | Redirect alias to `my_challenges#personal-tasks` |
| `daily-tasks/` | `daily_tasks` | Marks a task complete or adds cumulative progress; JSON under AJAX, redirect otherwise |
| `save-task/<id>/` | `save_task` | Create or update a task inside an owned challenge |
| `copy/<id>/` | `copy_challenge` | Copies a visible challenge as a personal one |

### Access logic

| Action | Who |
|---|---|
| Create a non-personal challenge | Leaders (`LEADER`, `LEADER_PRO`) |
| Create a personal challenge | Any level |
| Edit or delete an owned challenge | Owner |
| Delete any challenge | Roles satisfying `can_delete_challenge` |
| Copy a visible challenge | Any user with visibility |
| Join a `unique` challenge | Only when no other `unique` challenge is active |

## Configuration and Dependencies

This app requires **no dedicated settings** and has **no external service integration** — no Redis,
Celery, Sentry, or Cloudflare usage of its own. Notifications are delegated to `core.utils.notifications`,
which owns the Redis and Celery side.

Constants it relies on come from `core.const`: `PERSONAL_CHALLENGE_NAME`, `MAX_CHALLENGES_PER_USER`,
`DAILY`, `MONTHLY`.

App dependencies: `core`, `main` (`Incentive`, notification templates), `user_levels`, `users`.

> `UserChallengeProgress.unique_together` was originally declared as a class attribute rather than
> inside `Meta`, so the constraint only became effective with migration `0022`.
