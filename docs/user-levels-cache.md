# Redis cache for `user_levels`

Operational reference for the cache layer that speeds up level resolution and sponsor-tree traversal.
The functional contract of the level system (models, `capabilities`, visibility policy, downgrade
lifecycle) lives in [`apps/user_levels/README.md`](../apps/user_levels/README.md); this document
covers only the cache infrastructure, its invalidation and how to debug it.

Cached data:

- A user's effective level (`basic` / `pro` / `leader` / `leader_pro`).
- The downline tree below a given top sponsor.

## Redis configuration

### Relevant settings

In `Platform/settings.py`:

```python
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

# Key prefix (used by apps/core/utils/redis_bd.py)
REDIS_KEY_PREFIX = env("REDIS_KEY_PREFIX", default="platform:")

# Default TTL (seconds) for the level cache and related structures
USER_LEVEL_CACHE_TTL = env.int("USER_LEVEL_CACHE_TTL", default=300)
```

Under Docker, `REDIS_URL` points at the compose `redis` service. See [`docs/docker.md`](docker.md).

### Helpers (`apps/core/utils/redis_bd.py`)

| Helper | Purpose |
|---|---|
| `redis_client` | `redis.Redis.from_url(settings.REDIS_URL)` |
| `redis_get(key)` | Reads JSON, applying `REDIS_KEY_PREFIX` |
| `redis_set(key, value, ex=None)` | Writes JSON with a TTL (`USER_LEVEL_CACHE_TTL` by default) |
| `redis_delete_key(key)` | Deletes a single key |
| `redis_delete_pattern(pattern)` | Deletes by pattern (`SCAN` + `DEL`), relative to the prefix |
| `acquire_processing_flag(name, ttl)` / `release_processing_flag` / `processing_flag_exists` | TTL locks for idempotent jobs |

## Cache keys

All keys are written under `REDIS_KEY_PREFIX` (`platform:` by default).

| Key | Built by | Contents |
|---|---|---|
| `user_levels:user_level:{user_id}` | `_user_level_cache_key` | `{"code": "basic\|pro\|leader\|leader_pro", "level_id": <id\|null>}` |
| `user_levels:downline:{top_user_id}:{level_top\|none}` | `_downline_cache_key` | `[<user_id>, ...]` for the subtree below that sponsor |

Both helpers live in `apps/user_levels/levels.py`. The downline key embeds the cut-off level
(`level_top`, `leader_pro` by default) because the same user yields different trees depending on
where the traversal stops.

Only minimal data is persisted (`code` and `level_id`); the `Level` instance is loaded lazily from
the database when `EffectiveLevel.level_obj` is accessed.

## Invalidation and `transaction.on_commit`

Invalidation is centralised in `apps/user_levels/signals.py` and always runs **after the commit**, so
that a concurrent read cannot repopulate the cache with uncommitted data.

### Global helper

```python
from apps.user_levels.levels import invalidate_all_user_related_caches

invalidate_all_user_related_caches(user_id=None)
```

It groups `invalidate_user_level_cache` + `invalidate_downline_user_ids_cache`. With a `user_id` it
invalidates only that user; without arguments it invalidates every key in the namespace.

### Signals

| Signal | Trigger | Action after commit |
|---|---|---|
| `sponsor_changed_invalidate_cache` | `post_save` on `User` with a modified `sponsor` (compared against the value cached in `pre_save` by `cache_old_sponsor`) | `invalidate_downline_user_ids_cache(None)` |
| `level_changed` / `level_deleted` | `post_save` / `post_delete` on `Level` | `invalidate_all_user_related_caches(None)` |
| `user_level_profile_changed` | `post_save` on `UserLevelProfile` | `invalidate_all_user_related_caches(None)` plus, depending on the rank comparison against `LEVEL_HIERARCHY`, `handle_leader_upgrade` or `handle_level_downgrade` |
| `user_level_profile_deleted` | `post_delete` on `UserLevelProfile` | `invalidate_all_user_related_caches(None)` |
| `ensure_user_level_profile` | `post_save` on `User` (creation) | Creates a `UserLevelProfile` at level `basic` |
| `init_levels_after_migrate` | `post_migrate` for `user_levels` | `sync_levels_from_defaults(...)` with a non-destructive `capabilities` merge |

A sponsor change or a `Level` change alters the topology for many users at once, so those cases
invalidate globally instead of trying to narrow down the affected subset.

## Synchronising the default levels

`DEFAULT_LEVELS` and its utilities live in `apps/user_levels/capabilities.py`:

- `ensure_default_levels()` — creates any missing levels.
- `sync_levels_from_defaults(update_existing=True, overwrite_fields=False, capabilities_mode="merge")`
  — creates missing levels and updates `capabilities` in `merge` mode (adding new keys without
  overwriting existing ones) or `replace`.

It is invoked automatically on `post_migrate`, so the base configuration lands in the database after
a migration with no manual steps.

## Debugging

### Basic check

```powershell
python manage.py check
```

### Level cache

```python
from apps.users.models import User
from apps.user_levels.levels import get_user_level

u = User.objects.first()
print(get_user_level(u))  # 1st call: miss -> DB + Redis
print(get_user_level(u))  # 2nd call: hit
```

```bash
redis-cli KEYS 'platform:user_levels:user_level:*'
redis-cli GET 'platform:user_levels:user_level:<user_id>'
```

### Invalidation on a level change

```python
from apps.user_levels.models import Level, LevelType, UserLevelProfile
from apps.user_levels.levels import get_user_level

prof = UserLevelProfile.objects.select_related("level", "user").first()
print(get_user_level(prof.user).code)

prof.level = Level.objects.get(code=LevelType.PRO)
prof.save()  # invalidated on_commit

print(get_user_level(prof.user).code)  # reflects the new level
```

Under Docker, prefix these commands with the matching service
(`docker compose exec web python manage.py shell`, `docker compose exec redis redis-cli`).
