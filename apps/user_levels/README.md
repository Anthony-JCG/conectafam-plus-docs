# user_levels

## Description

Subscription-based access control engine and one of the two core apps of the monolith. It owns every
rule about **what a user may do and what a user may see**: effective level, capability limits and
scopes, restricted routes, sponsor-tree traversal, shared-content visibility down the downline, and
the full downgrade lifecycle.

No other app replicates these rules. Business apps call the public API described below; if a resource
can be shared, its queryset **must** come from `get_model_visible_queryset` (or a specific variant)
rather than a plain `Model.objects.filter(user=request.user)`.

Relationship to `users.User`: `UserLevelProfile` is a OneToOne extension of the user, created
automatically on registration. The sponsor tree traversed here is `User.sponsor`, the
self-referential FK that structures the whole ecosystem.

Redis caching details (keys, TTL, invalidation semantics, debugging recipes) are documented
separately in [`docs/user-levels-cache.md`](../../docs/user-levels-cache.md).

## Models and Data

### `Level`

Subscription level configuration, identified by `code` (`LevelType`).

Key fields: `id_product_stripe`, `monthly_price`, `yearly_price`, `id_monthly_price_stripe`,
`id_yearly_price_stripe`, `capabilities` (JSONField).

Key methods:

- `get_capability(model_key, action, default=None)` — reads a capability dict.
- `set_capability(model_key, action, **kwargs)` — writes a capability and saves.
- `get_limit_levels(model_key)` — class method; `{level: limit}` for non-leader-pro levels (`0` when
  not allowed, `None` when unlimited).
- `get_prices()` — monthly/yearly prices, fetched from Stripe when the price IDs are set.

### `UserLevelProfile`

OneToOne with `User`, created by the `ensure_user_level_profile` signal.

| Field | Type | Notes |
|---|---|---|
| `level` | FK → `Level` | Active subscription level |
| `share_enabled` | bool | Leader Pro only; reserved for downline-cut control |
| `was_downgraded` | bool | User was downgraded from leader |
| `was_leader_when_downgraded` | bool | Distinguishes leader downgrade from pro→basic; used in top-sponsor search |
| `downgrade_task_id` | str | Celery task ID for scheduled object deletion |
| `free_trial_active` | bool | Active free trial |
| `free_trial_ends_at` | datetime | Trial expiry |
| `free_trial_task_id` | str | Celery task ID for `end_free_trial` |

### `SharedObjectRecord`

Legacy bookkeeping. **No longer drives visibility** — shared content is resolved through the
creator-chain policy — and since the Leader Pro copy-offer flow was removed **no code writes to it
any more**; only historical rows remain. They are still read during downgrade cleanup and removed by
a `post_delete` receiver wired to every model in `core.const.OBJECT_TYPE_CHOICES`.

Fields: `leader` (FK → `User`), `object_type`, `object_id`, `shared_at`.

### `DowngradedObjectFlag`

Marks a downgraded user's objects for deferred deletion.
Fields: `owner` (FK → `User`), `object_type`, `object_id`, `marked_at`, `delete_at`.

### `LeaderDowngradeCopyOffer`

Record created for every descendant when an upline leader is downgraded, granting them the right to
take over that leader's resources. Fields: `source_leader`, `target_user`, `created_at`.

The offer is **not accepted through a form**. It is settled implicitly: the countdown is the
`DowngradedObjectFlag.delete_at` grace window, and a target user who reaches `leader` or `leader_pro`
before it expires gets a copy of every flagged object through `handle_leader_upgrade`. If nobody
upgrades, Celery deletes the flagged objects when the countdown ends.

### `RestrictedAccessAlert`

Configurable copy for the "upgrade required" modals. Cached; invalidated by signal on save/delete.

### Level hierarchy and capabilities

Ascending order: `basic` → `pro` → `leader` → `leader_pro` (`LevelType` in `models.py`,
`LEVEL_HIERARCHY` in `levels.py`).

```json
{
  "challenge": {
    "create": { "allowed": true, "limit": 4, "scope": "mixed", "share_downline": true },
    "delete": { "own_only": true }
  },
  "restricted_routes": ["boards_home", "save_board"]
}
```

- `model_key` — logical model key; constants in `const.py` (`CHALLENGE_MODEL_KEY`, `TASK_MODEL_KEY`,
  `STREAM_MODEL_KEY`, `FOLLOW_UP_MESSAGE_MODEL_KEY`, `KEYBOARD_API_MODEL_KEY`…).
- `scope` — `"personal_only"` | `"shared_only"` | `"mixed"`.
- `restricted_routes` — `url_name` values the level cannot visit.

To extend capabilities, edit `DEFAULT_LEVELS` in `capabilities.py` and add a data migration. **Do not
add columns to `Level`.**

### Visibility policy

Leader-created content propagates down the sponsor tree until the next **Leader Pro** cut (see
`iter_descendants`, `get_top_sponsor`). `get_model_visible_queryset` returns:

1. Objects the viewer created.
2. Objects from the **leader anchor** — nearest leader (or downgraded leader) upline, including self.
3. Objects from the **Leader Pro anchor** above that cut, when not already included.

Intermediate leaders who duplicated content do not produce duplicate listings: a downline user sees
one effective creator chain, not every ancestor leader.

**PRO streaming exception:** a PRO user may create a derivative stream (`parent_stream` FK) from a
visible upline original through `use_shared_stream`. The derivative is personal; the original remains
the shared source for the line.

## Views and Frontend Integration

**This app has no `views.py`, no `urls.py` and no HTMX.** It is a pure domain layer: it owns no
route and renders no page of its own. Its frontend surface is entirely indirect:

- `RouteLevelAccessMiddleware` gates every request by level, raising `Http404` when
  `is_route_allowed()` is `False` for an authenticated user. It is the app's only entry in
  `settings.MIDDLEWARE`.
- `templatetags/restricted_access_tags.py` renders the "upgrade required" modals in any template,
  backed by `RestrictedAccessAlert` and `restricted_access.py`.
- `RESTRICTED_ALERT_*` constants from `const.py` are injected into other apps' template contexts
  (`links`, `landing`) to drive those modals.

### Services

`services/object_copy.py` holds the deep-copy primitives used by the downgrade/upgrade lifecycle:
`duplicate_instance_by_pk`, `copy_tasks_for_parent`, `copy_sections_for_category` and
`copy_post_finalization`. They are consumed exclusively by `downgrade.py`; they duplicate a row
together with its children and, where relevant, its files in storage.

## Configuration and Dependencies

| Setting | Purpose |
|---|---|
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Backing store for level and downline caches |
| `USER_LEVEL_CACHE_TTL` | Default TTL (seconds) for those keys |
| `STRIPE_API_KEY` / `STRIPE_SECRET_KEY` | Read indirectly through `pricing` when `Level.get_prices()` resolves Stripe prices |

Cache keys:

| Key | Populated by | Contents |
|---|---|---|
| `user_levels:user_level:<user_id>` | `get_user_level` | `{code, level_id}` |
| `user_levels:downline:<user_id>:<level_top\|none>` | `get_downline_user_ids` | `[int, ...]` |

App dependencies:

| Module | Usage |
|---|---|
| `users` | `User` and its `sponsor` FK; level properties consumed on the model |
| `pricing` | Stripe prices via lazy import inside `Level.get_prices` |
| `core` | `OBJECT_TYPE_CHOICES`, Redis helpers |
| `challenge`, `main`, `training`, `streaming`, `landing`, `boards` | Resolved during downgrade cleanup and the upgrade copy in `services/object_copy.py` |
| Redis | Level and downline caches, restricted-access alerts |
| Celery | `end_free_trial`, `cleanup_user_downgraded_objects` |

This app has **no Sentry or Cloudflare integration** of its own.

### Public API

Import from `apps.user_levels.levels`, `.permissions`, `.capabilities`, or `.utils`.

| Function | Module | Description |
|---|---|---|
| `get_user_level(user)` | `levels` | Effective level; Redis-cached |
| `get_top_sponsor(user, level_top, …)` | `levels` | Nearest upline user at `level_top`, or the root |
| `get_downline_user_ids(user, level_top)` | `levels` | Subtree IDs, stopping at `leader_pro` nodes |
| `iter_descendants(root, level_top)` | `levels` | Generator over the subtree, cutting at `level_top` |
| `get_visible_creator_ids(user, …)` | `levels` | Creator IDs for the visibility policy |
| `get_model_visible_queryset(user, Model, …)` | `levels` | Objects of `Model` visible to `user` |
| `get_challenge_visible_queryset(user, Model, …)` | `levels` | As above, excluding other users' default personal challenges |
| `invalidate_all_user_related_caches(user_id)` | `levels` | Call after changing level, profile, or sponsor |
| `check_action_allowed(user, model_key, action, …)` | `permissions` | Raises `PermissionDenied`; evaluates `allowed`, `scope`, `limit`, `own_only` |
| `is_route_allowed(user, url_name)` | `permissions` | `False` when the route is in `restricted_routes` |
| `can_delete_challenge(user, owner_id)` | `permissions` | Ownership or unrestricted delete permission |
| `collect_downgrade_blocks(user, labels)` | `utils` | Blocked object IDs from `DowngradedObjectFlag` |

### Downgrade lifecycle

| Function | Module | Description |
|---|---|---|
| `handle_level_downgrade(user, old_code, new_code)` | `downgrade` | Marks excess/owned objects and schedules Celery cleanup. Leader downgrade: 7-day grace + downline offers. Pro→Basic: 24 h grace |
| `handle_leader_upgrade(user)` | `downgrade` | Clears downgrade flags; copies marked objects from downgraded ancestors only |
| `reconcile_excess_objects_for_all_users(grace_hours)` | `downgrade` | One-shot alignment after capability changes |

Excess detection covers every limited `model_key`: `task`, `challenge`, `message`,
`follow_up_message`, `whatsapp_link`, `scheduled_task`, `stream`, `landing_page`, `boards`.

Flow: `collect_downgrade_blocks` powers UI warnings → the `UserLevelProfile` signal calls
`handle_level_downgrade`, which flags the objects and creates a `LeaderDowngradeCopyOffer` per
descendant → any descendant promoted to leader before `delete_at` copies the flagged objects via
`handle_leader_upgrade` → at `delete_at`, Celery deletes whatever is left and resets the state.

### Signals

Everything hangs off `UserLevelProfile`, not `User`: `cache_old_level` stores the previous level code
on `pre_save`, and `user_level_profile_changed` compares it against the new one on `post_save`. All
side effects run inside `transaction.on_commit`, so nothing fires on a rolled-back save.

| Signal | Trigger | Action |
|---|---|---|
| `ensure_user_level_profile` | `User` created | Creates the profile with level `basic` |
| `cache_old_level` | `UserLevelProfile` `pre_save` | Stores `_old_level_code` for the comparison below |
| `user_level_profile_changed` | `UserLevelProfile` saved | Invalidates caches and dispatches on the level delta (see next table) |
| `sponsor_changed_invalidate_cache` | `User.sponsor` changed | Invalidates the downline cache (guarded by `cache_old_sponsor` on `pre_save`) |
| `level_changed` / `level_deleted` | `Level` saved/deleted | Global cache invalidation |
| `_cleanup` | Any model in `OBJECT_TYPE_CHOICES` deleted | Removes its `SharedObjectRecord` rows |
| `init_levels_after_migrate` | `post_migrate` | `sync_levels_from_defaults` with non-destructive capability merge |
| `restricted_access_alert_changed` | `RestrictedAccessAlert` saved/deleted | Invalidates the alerts cache |

#### What happens on a level change

`user_level_profile_changed` ranks both codes against `LEVEL_HIERARCHY` and branches:

| Transition | Effect |
|---|---|
| `basic`/`pro` → `leader`/`leader_pro` | `handle_leader_upgrade`: clears the user's own downgrade flags and copies every object flagged on a downgraded ancestor, honouring the pending `LeaderDowngradeCopyOffer` |
| Any rank decrease | `handle_level_downgrade`: flags excess and owned objects with a `delete_at`, schedules the Celery cleanup, warns the user and — for a leader — alerts the downline and opens a `LeaderDowngradeCopyOffer` for each descendant |
| Any rank increase from a previously downgraded profile | Still-excess objects are re-evaluated with `_update_excess_objects_for_current_level`; if no leader flags remain, `reset_downgrade_state` revokes the pending Celery task and clears `was_downgraded` |
| Same rank / unknown code | Cache invalidation only |

### Management commands

- `reconcile_excess_objects` — aligns object counts with current capability limits.
- `resend_subscription_correction_emails` — reissues subscription-correction notices.
- `subscription_correction.run_subscription_correction(dry_run=True)` — audits Stripe vs DB levels
  from the Django shell.
