# Caché Redis de `user_levels`

Referencia operativa de la capa de caché que acelera la resolución de nivel y el recorrido del árbol de patrocinio.
El contrato funcional del sistema de niveles (modelos, `capabilities`, política de visibilidad, ciclo de vida
de degradación) está en [`apps/user_levels/README.es.md`](../apps/user_levels/README.es.md); este documento
cubre solo la infraestructura de caché, su invalidación y cómo depurarla.

Datos en caché:

- El nivel efectivo de un usuario (`basic` / `pro` / `leader` / `leader_pro`).
- El árbol de línea descendente bajo un patrocinador raíz determinado.

## Configuración de Redis

### Ajustes relevantes

En `Platform/settings.py`:

```python
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

# Key prefix (used by apps/core/utils/redis_bd.py)
REDIS_KEY_PREFIX = env("REDIS_KEY_PREFIX", default="platform:")

# Default TTL (seconds) for the level cache and related structures
USER_LEVEL_CACHE_TTL = env.int("USER_LEVEL_CACHE_TTL", default=300)
```

En Docker, `REDIS_URL` apunta al servicio `redis` de Compose. Ver [`docs/docker.es.md`](docker.es.md).

### Helpers (`apps/core/utils/redis_bd.py`)

| Helper | Propósito |
|---|---|
| `redis_client` | `redis.Redis.from_url(settings.REDIS_URL)` |
| `redis_get(key)` | Lee JSON aplicando `REDIS_KEY_PREFIX` |
| `redis_set(key, value, ex=None)` | Escribe JSON con un TTL (`USER_LEVEL_CACHE_TTL` por defecto) |
| `redis_delete_key(key)` | Elimina una sola clave |
| `redis_delete_pattern(pattern)` | Elimina por patrón (`SCAN` + `DEL`), relativo al prefijo |
| `acquire_processing_flag(name, ttl)` / `release_processing_flag` / `processing_flag_exists` | Bloqueos con TTL para trabajos idempotentes |

## Claves de caché

Todas las claves se escriben bajo `REDIS_KEY_PREFIX` (`platform:` por defecto).

| Clave | Construida por | Contenido |
|---|---|---|
| `user_levels:user_level:{user_id}` | `_user_level_cache_key` | `{"code": "basic\|pro\|leader\|leader_pro", "level_id": <id\|null>}` |
| `user_levels:downline:{top_user_id}:{level_top\|none}` | `_downline_cache_key` | `[<user_id>, ...]` del subárbol bajo ese patrocinador |

Ambos helpers viven en `apps/user_levels/levels.py`. La clave de línea descendente incorpora el nivel de corte
(`level_top`, `leader_pro` por defecto) porque el mismo usuario produce árboles distintos según
dónde se detenga el recorrido.

Solo se persisten datos mínimos (`code` y `level_id`); la instancia de `Level` se carga de forma diferida
desde la base de datos cuando se accede a `EffectiveLevel.level_obj`.

## Invalidación y `transaction.on_commit`

La invalidación está centralizada en `apps/user_levels/signals.py` y siempre se ejecuta **después del commit**,
para que una lectura concurrente no pueda rellenar la caché con datos aún no confirmados.

### Helper global

```python
from apps.user_levels.levels import invalidate_all_user_related_caches

invalidate_all_user_related_caches(user_id=None)
```

Agrupa `invalidate_user_level_cache` + `invalidate_downline_user_ids_cache`. Con un `user_id`
invalida solo a ese usuario; sin argumentos invalida todas las claves del espacio de nombres.

### Señales

| Señal | Disparador | Acción tras el commit |
|---|---|---|
| `sponsor_changed_invalidate_cache` | `post_save` en `User` con `sponsor` modificado (comparado con el valor cacheado en `pre_save` por `cache_old_sponsor`) | `invalidate_downline_user_ids_cache(None)` |
| `level_changed` / `level_deleted` | `post_save` / `post_delete` en `Level` | `invalidate_all_user_related_caches(None)` |
| `user_level_profile_changed` | `post_save` en `UserLevelProfile` | `invalidate_all_user_related_caches(None)` y, según la comparación de rango con `LEVEL_HIERARCHY`, `handle_leader_upgrade` o `handle_level_downgrade` |
| `user_level_profile_deleted` | `post_delete` en `UserLevelProfile` | `invalidate_all_user_related_caches(None)` |
| `ensure_user_level_profile` | `post_save` en `User` (creación) | Crea un `UserLevelProfile` en nivel `basic` |
| `init_levels_after_migrate` | `post_migrate` de `user_levels` | `sync_levels_from_defaults(...)` con un merge no destructivo de `capabilities` |

Un cambio de patrocinador o de `Level` altera la topología de muchos usuarios a la vez, por eso esos casos
invalidan de forma global en lugar de intentar delimitar el subconjunto afectado.

## Sincronización de los niveles por defecto

`DEFAULT_LEVELS` y sus utilidades viven en `apps/user_levels/capabilities.py`:

- `ensure_default_levels()` — crea los niveles que falten.
- `sync_levels_from_defaults(update_existing=True, overwrite_fields=False, capabilities_mode="merge")`
  — crea los niveles faltantes y actualiza `capabilities` en modo `merge` (añade claves nuevas sin
  sobrescribir las existentes) o `replace`.

Se invoca automáticamente en `post_migrate`, de modo que la configuración base queda en la base de datos
tras una migración sin pasos manuales.

## Depuración

### Comprobación básica

```powershell
python manage.py check
```

### Caché de nivel

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

### Invalidación al cambiar de nivel

```python
from apps.user_levels.models import Level, LevelType, UserLevelProfile
from apps.user_levels.levels import get_user_level

prof = UserLevelProfile.objects.select_related("level", "user").first()
print(get_user_level(prof.user).code)

prof.level = Level.objects.get(code=LevelType.PRO)
prof.save()  # invalidated on_commit

print(get_user_level(prof.user).code)  # reflects the new level
```

En Docker, antepone a estos comandos el servicio correspondiente
(`docker compose exec web python manage.py shell`, `docker compose exec redis redis-cli`).
