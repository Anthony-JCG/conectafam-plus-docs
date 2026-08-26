# challenge

## Descripción

Retos y sus tareas recurrentes diarias/mensuales. Los usuarios crean retos, se unen a los que
comparte su líder de línea ascendente y registran el progreso por tarea y fecha. Admite tanto retos
compartidos por el líder como listas de tareas puramente personales.

Relación con las apps núcleo:

- **`user_levels`** — la visibilidad viene de `get_challenge_visible_queryset`, los permisos de
  `check_action_allowed` y `can_delete_challenge`, y las restricciones por degradación de
  `collect_downgrade_blocks`. Si un reto puede ser no personal es una decisión de nivel, no de esta
  app.
- **`core`** — constantes (`PERSONAL_CHALLENGE_NAME`, `MAX_CHALLENGES_PER_USER`), helpers de
  notificación (`notify_downline`, `send_personal_notification`) y utilidades de programación por
  día (`get_tasks_for_day`).
- **`users.User`** — propietario de los retos y de todos los registros de progreso.
- **`main`** — un `Task` puede pertenecer a un `main.Incentive` en lugar de a un `Challenge`.

## Modelos y datos

### `Challenge`

Creado por un usuario; personal (privado) o compartido con la línea descendente. FK → `users.User`.

| Campo | Notas |
|---|---|
| `challenge_collect_type` | `unique` — solo uno activo por usuario; `set` — se permiten varios |
| `challenge_type` | `static` — se reinicia el día 1 del mes; `dynamic` — arranca desde la fecha de incorporación |
| `is_personal` | Lo oculta de la línea descendente; forzado a true para usuarios que no son líderes |

### `Task`

Pertenece a un `Challenge` **o** a un `main.Incentive` — mutuamente excluyentes, validados en
`clean()`. El campo `day` gobierna la programación (`"1-31"`, `"1-15"`, …) y lo parsea
`core.utils.task_days`.

### `UserChallengeProgress`

Registra la participación activa. FK → `users.User`, FK → `Challenge`;
`unique_together = ("user", "challenge")`.

`get_daily_tasks()` devuelve las tareas de hoy con su estado de completado, resolviendo el progreso
con una **única consulta en bloque** para evitar N+1 al renderizar las tarjetas de tareas.

### `UserTaskProgress`

Por usuario, por tarea, por fecha. `unique_together = ("user", "task", "date")`.

- Tareas diarias: `date = today`.
- Tareas mensuales: `date = primer día del mes`, canonizado por
  `services.get_or_update_task_progress`.

### `UserTaskOrder`

Ordenación personalizada de tareas por usuario. FK → `users.User`, FK → `Task`. Reservado para uso
futuro.

### Servicios (`services.py`)

| Función | Descripción |
|---|---|
| `copy_challenge_with_tasks(user, source)` | Copia en profundidad un reto y sus tareas con `bulk_create`. La copia es siempre personal |
| `get_or_update_task_progress(user, task, date, *, mark_complete, progress_value)` | Obtiene o crea la fila de progreso y aplica la mutación, gestionando la canonización de fechas diarias/mensuales |
| `deactivate_orphan_unique_progresses(user)` | Desactiva filas de progreso tipo `unique` que quedan sin un reto activo válido |

`utils.get_progress_challenge_user` filtra los progresos activos visibles.

## Vistas e integración frontend

**Esta app no usa HTMX.** No hay atributos `hx-*` en sus plantillas ni ramas `request.htmx` en sus
vistas. La interacción combina posts de formulario estándar y un endpoint AJAX que responde
`JsonResponse` cuando la petición lleva `X-Requested-With: XMLHttpRequest`.

Prefijo de URL: **`/challenges/`**

| URL | Vista | Descripción |
|---|---|---|
| `""` | `challenges` | POST crea un reto; GET redirige a `my_challenges#manage-challenges` |
| `edit/<id>/` | `edit_challenge` | Editar un reto y su lista de tareas |
| `delete-challenge/` | `delete_challenge` | Borrar un reto o una tarea |
| `my-challenges/` | `my_challenges` | Vista unificada: unirse/salir, panel de administración, tareas personales |
| `my-tasks/` | `my_tasks` | Alias de redirección a `my_challenges#personal-tasks` |
| `daily-tasks/` | `daily_tasks` | Marca una tarea como completada o añade progreso acumulativo; JSON bajo AJAX, redirect en caso contrario |
| `save-task/<id>/` | `save_task` | Crear o actualizar una tarea dentro de un reto propio |
| `copy/<id>/` | `copy_challenge` | Copia un reto visible como personal |

### Lógica de acceso

| Acción | Quién |
|---|---|
| Crear un reto no personal | Líderes (`LEADER`, `LEADER_PRO`) |
| Crear un reto personal | Cualquier nivel |
| Editar o borrar un reto propio | Propietario |
| Borrar cualquier reto | Roles que satisfacen `can_delete_challenge` |
| Copiar un reto visible | Cualquier usuario con visibilidad |
| Unirse a un reto `unique` | Solo cuando no hay otro reto `unique` activo |

## Configuración y dependencias

Esta app **no requiere settings dedicados** y **no tiene integración con servicios externos** — ni
Redis, Celery, Sentry ni Cloudflare propios. Las notificaciones se delegan a
`core.utils.notifications`, que posee el lado Redis y Celery.

Las constantes de las que depende vienen de `core.const`: `PERSONAL_CHALLENGE_NAME`,
`MAX_CHALLENGES_PER_USER`, `DAILY`, `MONTHLY`.

Dependencias de la app: `core`, `main` (`Incentive`, plantillas de notificación), `user_levels`,
`users`.

> `UserChallengeProgress.unique_together` se declaró originalmente como atributo de clase en lugar
> de dentro de `Meta`, así que la restricción solo pasó a ser efectiva con la migración `0022`.
