# user_levels

## Descripción

Motor de control de acceso basado en suscripción y una de las dos apps núcleo del monolito. Posee
todas las reglas sobre **qué puede hacer un usuario y qué puede ver**: nivel efectivo, límites y
alcances de capabilities, rutas restringidas, recorrido del árbol de patrocinio, visibilidad de
contenido compartido hacia la línea descendente y el ciclo completo de degradación.

Ninguna otra app replica estas reglas. Las apps de negocio llaman a la API pública descrita más
abajo; si un recurso puede compartirse, su queryset **debe** proceder de
`get_model_visible_queryset` (o de una variante específica) y no de un simple
`Model.objects.filter(user=request.user)`.

Relación con `users.User`: `UserLevelProfile` es una extensión OneToOne del usuario, creada
automáticamente al registrarse. El árbol de patrocinio que se recorre aquí es `User.sponsor`, la FK
autorreferencial que estructura todo el ecosistema.

Los detalles de caché Redis (claves, TTL, semántica de invalidación, recetas de depuración) están
documentados por separado en [`docs/user-levels-cache.es.md`](../../docs/user-levels-cache.es.md).

## Modelos y datos

### `Level`

Configuración de nivel de suscripción, identificada por `code` (`LevelType`).

Campos clave: `id_product_stripe`, `monthly_price`, `yearly_price`, `id_monthly_price_stripe`,
`id_yearly_price_stripe`, `capabilities` (JSONField).

Métodos clave:

- `get_capability(model_key, action, default=None)` — lee un dict de capability.
- `set_capability(model_key, action, **kwargs)` — escribe una capability y guarda.
- `get_limit_levels(model_key)` — método de clase; `{level: limit}` para niveles que no son
  leader-pro (`0` cuando no está permitido, `None` cuando es ilimitado).
- `get_prices()` — precios mensual/anual, obtenidos de Stripe cuando los IDs de precio están
  definidos.

### `UserLevelProfile`

OneToOne con `User`, creado por el signal `ensure_user_level_profile`.

| Campo | Tipo | Notas |
|---|---|---|
| `level` | FK → `Level` | Nivel de suscripción activo |
| `share_enabled` | bool | Solo Leader Pro; reservado para el control de corte de línea |
| `was_downgraded` | bool | El usuario fue degradado desde líder |
| `was_leader_when_downgraded` | bool | Distingue degradación de líder de pro→basic; usado en la búsqueda del top sponsor |
| `downgrade_task_id` | str | ID de tarea Celery para el borrado programado de objetos |
| `free_trial_active` | bool | Prueba gratuita activa |
| `free_trial_ends_at` | datetime | Caducidad de la prueba |
| `free_trial_task_id` | str | ID de tarea Celery para `end_free_trial` |

### `SharedObjectRecord`

Contabilidad legada. **Ya no impulsa la visibilidad** — el contenido compartido se resuelve mediante
la política de cadena de creadores — y desde que se eliminó el flujo de oferta de copia Leader Pro
**ningún código escribe en él**; solo quedan filas históricas. Aún se leen durante la limpieza de
degradación y las elimina un receptor `post_delete` cableado a cada modelo de
`core.const.OBJECT_TYPE_CHOICES`.

Campos: `leader` (FK → `User`), `object_type`, `object_id`, `shared_at`.

### `DowngradedObjectFlag`

Marca los objetos de un usuario degradado para borrado diferido.
Campos: `owner` (FK → `User`), `object_type`, `object_id`, `marked_at`, `delete_at`.

### `LeaderDowngradeCopyOffer`

Registro creado por cada descendiente cuando se degrada un líder de línea ascendente, otorgándoles
el derecho a hacerse cargo de los recursos de ese líder. Campos: `source_leader`, `target_user`,
`created_at`.

La oferta **no se acepta mediante un formulario**. Se resuelve de forma implícita: la cuenta atrás
es la ventana de gracia `DowngradedObjectFlag.delete_at`, y un usuario destino que alcance `leader`
o `leader_pro` antes de que expire recibe una copia de cada objeto marcado a través de
`handle_leader_upgrade`. Si nadie asciende, Celery borra los objetos marcados al terminar la cuenta
atrás.

### `RestrictedAccessAlert`

Textos configurables para los modales de «se requiere actualización de plan». En caché; se invalida
por signal al guardar/borrar.

### Jerarquía de niveles y capabilities

Orden ascendente: `basic` → `pro` → `leader` → `leader_pro` (`LevelType` en `models.py`,
`LEVEL_HIERARCHY` en `levels.py`).

```json
{
  "challenge": {
    "create": { "allowed": true, "limit": 4, "scope": "mixed", "share_downline": true },
    "delete": { "own_only": true }
  },
  "restricted_routes": ["boards_home", "save_board"]
}
```

- `model_key` — clave lógica de modelo; constantes en `const.py` (`CHALLENGE_MODEL_KEY`,
  `TASK_MODEL_KEY`, `STREAM_MODEL_KEY`, `FOLLOW_UP_MESSAGE_MODEL_KEY`, `KEYBOARD_API_MODEL_KEY`…).
- `scope` — `"personal_only"` | `"shared_only"` | `"mixed"`.
- `restricted_routes` — valores `url_name` que el nivel no puede visitar.

Para ampliar capabilities, edita `DEFAULT_LEVELS` en `capabilities.py` y añade una migración de
datos. **No añadas columnas a `Level`.**

### Política de visibilidad

El contenido creado por líderes se propaga por el árbol de patrocinio hasta el siguiente corte
**Leader Pro** (véase `iter_descendants`, `get_top_sponsor`). `get_model_visible_queryset` devuelve:

1. Objetos que el visitante creó.
2. Objetos del **ancla líder** — el líder (o líder degradado) más cercano en línea ascendente,
   incluyéndose a sí mismo.
3. Objetos del **ancla Leader Pro** por encima de ese corte, cuando aún no están incluidos.

Los líderes intermedios que duplicaron contenido no generan listados duplicados: un usuario de línea
descendente ve una cadena efectiva de creadores, no cada líder ancestro.

**Excepción de streaming PRO:** un usuario PRO puede crear un stream derivado (`parent_stream` FK)
a partir de un original visible de línea ascendente mediante `use_shared_stream`. El derivado es
personal; el original sigue siendo la fuente compartida de la línea.

## Vistas e integración frontend

**Esta app no tiene `views.py`, ni `urls.py` ni HTMX.** Es una capa de dominio pura: no posee
ninguna ruta ni renderiza página propia. Su superficie frontend es enteramente indirecta:

- `RouteLevelAccessMiddleware` filtra cada petición por nivel, lanzando `Http404` cuando
  `is_route_allowed()` es `False` para un usuario autenticado. Es la única entrada de la app en
  `settings.MIDDLEWARE`.
- `templatetags/restricted_access_tags.py` renderiza los modales de «se requiere actualización» en
  cualquier plantilla, respaldados por `RestrictedAccessAlert` y `restricted_access.py`.
- Las constantes `RESTRICTED_ALERT_*` de `const.py` se inyectan en los contextos de plantilla de
  otras apps (`links`, `landing`) para impulsar esos modales.

### Servicios

`services/object_copy.py` contiene las primitivas de copia profunda usadas por el ciclo de
degradación/ascenso: `duplicate_instance_by_pk`, `copy_tasks_for_parent`,
`copy_sections_for_category` y `copy_post_finalization`. Las consume exclusivamente `downgrade.py`;
duplican una fila junto con sus hijos y, cuando corresponde, sus ficheros en el almacenamiento.

## Configuración y dependencias

| Setting | Propósito |
|---|---|
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Almacén de las cachés de nivel y de línea descendente |
| `USER_LEVEL_CACHE_TTL` | TTL por defecto (segundos) de esas claves |
| `STRIPE_API_KEY` / `STRIPE_SECRET_KEY` | Lectura indirecta a través de `pricing` cuando `Level.get_prices()` resuelve precios de Stripe |

Claves de caché:

| Clave | Poblada por | Contenido |
|---|---|---|
| `user_levels:user_level:<user_id>` | `get_user_level` | `{code, level_id}` |
| `user_levels:downline:<user_id>:<level_top\|none>` | `get_downline_user_ids` | `[int, ...]` |

Dependencias de apps:

| Módulo | Uso |
|---|---|
| `users` | `User` y su FK `sponsor`; propiedades de nivel consumidas en el modelo |
| `pricing` | Precios Stripe vía importación diferida dentro de `Level.get_prices` |
| `core` | `OBJECT_TYPE_CHOICES`, helpers de Redis |
| `challenge`, `main`, `training`, `streaming`, `landing`, `boards` | Resueltos durante la limpieza de degradación y la copia de ascenso en `services/object_copy.py` |
| Redis | Cachés de nivel y de línea descendente, alertas de acceso restringido |
| Celery | `end_free_trial`, `cleanup_user_downgraded_objects` |

Esta app **no tiene integración propia con Sentry ni Cloudflare**.

### API pública

Importar desde `apps.user_levels.levels`, `.permissions`, `.capabilities` o `.utils`.

| Función | Módulo | Descripción |
|---|---|---|
| `get_user_level(user)` | `levels` | Nivel efectivo; en caché Redis |
| `get_top_sponsor(user, level_top, …)` | `levels` | Usuario de línea ascendente más cercano en `level_top`, o la raíz |
| `get_downline_user_ids(user, level_top)` | `levels` | IDs del subárbol, deteniéndose en nodos `leader_pro` |
| `iter_descendants(root, level_top)` | `levels` | Generador sobre el subárbol, cortando en `level_top` |
| `get_visible_creator_ids(user, …)` | `levels` | IDs de creadores para la política de visibilidad |
| `get_model_visible_queryset(user, Model, …)` | `levels` | Objetos de `Model` visibles para `user` |
| `get_challenge_visible_queryset(user, Model, …)` | `levels` | Como arriba, excluyendo retos personales por defecto de otros usuarios |
| `invalidate_all_user_related_caches(user_id)` | `levels` | Llamar tras cambiar nivel, perfil o sponsor |
| `check_action_allowed(user, model_key, action, …)` | `permissions` | Lanza `PermissionDenied`; evalúa `allowed`, `scope`, `limit`, `own_only` |
| `is_route_allowed(user, url_name)` | `permissions` | `False` cuando la ruta está en `restricted_routes` |
| `can_delete_challenge(user, owner_id)` | `permissions` | Propiedad o permiso de borrado sin restricciones |
| `collect_downgrade_blocks(user, labels)` | `utils` | IDs de objetos bloqueados desde `DowngradedObjectFlag` |

### Ciclo de degradación

| Función | Módulo | Descripción |
|---|---|---|
| `handle_level_downgrade(user, old_code, new_code)` | `downgrade` | Marca objetos en exceso/propios y programa la limpieza Celery. Degradación de líder: gracia de 7 días + ofertas a la línea. Pro→Basic: gracia de 24 h |
| `handle_leader_upgrade(user)` | `downgrade` | Limpia flags de degradación; copia solo objetos marcados de ancestros degradados |
| `reconcile_excess_objects_for_all_users(grace_hours)` | `downgrade` | Alineación puntual tras cambios de capabilities |

La detección de exceso cubre cada `model_key` limitado: `task`, `challenge`, `message`,
`follow_up_message`, `whatsapp_link`, `scheduled_task`, `stream`, `landing_page`, `boards`.

Flujo: `collect_downgrade_blocks` alimenta las advertencias de UI → el signal de `UserLevelProfile`
llama a `handle_level_downgrade`, que marca los objetos y crea un `LeaderDowngradeCopyOffer` por
descendiente → cualquier descendiente promovido a líder antes de `delete_at` copia los objetos
marcados vía `handle_leader_upgrade` → en `delete_at`, Celery borra lo que quede y reinicia el
estado.

### Signals

Todo cuelga de `UserLevelProfile`, no de `User`: `cache_old_level` guarda el código de nivel
anterior en `pre_save`, y `user_level_profile_changed` lo compara con el nuevo en `post_save`. Todos
los efectos secundarios se ejecutan dentro de `transaction.on_commit`, de modo que nada se dispara
si el save se revierte.

| Signal | Disparador | Acción |
|---|---|---|
| `ensure_user_level_profile` | `User` creado | Crea el perfil con nivel `basic` |
| `cache_old_level` | `UserLevelProfile` `pre_save` | Guarda `_old_level_code` para la comparación siguiente |
| `user_level_profile_changed` | `UserLevelProfile` guardado | Invalida cachés y despacha según el delta de nivel (véase la tabla siguiente) |
| `sponsor_changed_invalidate_cache` | `User.sponsor` cambiado | Invalida la caché de línea descendente (protegido por `cache_old_sponsor` en `pre_save`) |
| `level_changed` / `level_deleted` | `Level` guardado/borrado | Invalidación global de caché |
| `_cleanup` | Cualquier modelo de `OBJECT_TYPE_CHOICES` borrado | Elimina sus filas `SharedObjectRecord` |
| `init_levels_after_migrate` | `post_migrate` | `sync_levels_from_defaults` con fusión no destructiva de capabilities |
| `restricted_access_alert_changed` | `RestrictedAccessAlert` guardado/borrado | Invalida la caché de alertas |

#### Qué ocurre al cambiar de nivel

`user_level_profile_changed` ordena ambos códigos respecto a `LEVEL_HIERARCHY` y ramifica:

| Transición | Efecto |
|---|---|
| `basic`/`pro` → `leader`/`leader_pro` | `handle_leader_upgrade`: limpia los flags de degradación propios del usuario y copia cada objeto marcado en un ancestro degradado, respetando el `LeaderDowngradeCopyOffer` pendiente |
| Cualquier descenso de rango | `handle_level_downgrade`: marca objetos en exceso y propios con un `delete_at`, programa la limpieza Celery, avisa al usuario y — si es líder — alerta a la línea y abre un `LeaderDowngradeCopyOffer` por cada descendiente |
| Cualquier ascenso de rango desde un perfil previamente degradado | Los objetos que siguen en exceso se reevalúan con `_update_excess_objects_for_current_level`; si no quedan flags de líder, `reset_downgrade_state` revoca la tarea Celery pendiente y limpia `was_downgraded` |
| Mismo rango / código desconocido | Solo invalidación de caché |

### Comandos de gestión

- `reconcile_excess_objects` — alinea el recuento de objetos con los límites de capability actuales.
- `resend_subscription_correction_emails` — reenvía avisos de corrección de suscripción.
- `subscription_correction.run_subscription_correction(dry_run=True)` — audita niveles Stripe vs BD
  desde el shell de Django.
