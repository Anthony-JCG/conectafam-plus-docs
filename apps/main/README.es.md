# main

## Descripción

El home autenticado de la plataforma: dashboard, gestión de equipo, programas de incentivos, la
ruta del distribuidor, estadísticas mensuales de captación y el centro de notificaciones. Es la app
en la que aterrizan los usuarios tras el login y la que agrega datos propiedad de las demás apps de
dominio.

Relación con las apps núcleo:

- **`users.User`** — cada modelo aquí está acotado a un usuario, y las vistas de equipo recorren el
  árbol `sponsor` directamente.
- **`user_levels`** — el CRUD de incentivos pasa por `check_action_allowed`, los listados por
  `get_model_visible_queryset` y las advertencias de degradación por `collect_downgrade_blocks`.
- **`core`** — constantes, helpers de payload Quill, utilidades de ficheros y el feed de
  notificaciones respaldado por Redis.

`main` lee de `challenge` (progreso de tareas en el dashboard), `communication` (tareas programadas
y contactos) y `training` (estadísticas de formación del equipo), lo que la convierte en la app más
expuesta al riesgo N+1; los helpers de `utils.py` existen para mantener esas agregaciones en un
número acotado de consultas.

## Modelos y datos

| Modelo | Propósito |
|---|---|
| `Notification` | Notificaciones persistentes por usuario (FK → `users.User`) |
| `TypeIncentive` | Catálogo ordenado de categorías de incentivo, gestionado desde admin |
| `Incentive` | Programa de incentivo: fechas, ubicación, descripción Quill, imagen de fondo (FK → `users.User`, FK → `TypeIncentive`) |
| `IncentiveFile` | Adjuntos; máximo 3 forzado en `save_incentive` |
| `UserFavoriteIncentive` | Tabla de unión de favoritos |
| `MonthlyAcquisitionStats` | Objetivos mensuales y contadores acumulados por usuario |
| `RouteStep` | Plantilla de paso de onboarding definida por el líder |
| `RouteStepProgress` | Compleción por distribuidor; dos FK a `users.User` (`distributor`, `tracker`) |
| `GeneralData` | Fila singleton con datos editables a nivel de sitio |

`challenge.Task` tiene una FK opcional a `Incentive`, que es cómo se representan las tareas mensuales
ligadas a incentivos.

### Servicios (`services/`)

| Módulo | Funciones clave |
|---|---|
| `notifications.py` | `notify_incentive_creation` — notificación personal, push a la línea y oferta de copia al líder, envuelto para que un fallo nunca revierta el guardado del incentivo |
| `incentives.py` | `copy_incentive_with_tasks`, `create_or_update_incentive_task`, `get_incentive_month_tasks`, `compute_incentive_type_order` |
| `route.py` | `resolve_route_owner`, `serialize_route_step`, `get_route_progress_ratio`, `attach_route_progress_to_children`, `build_distributor_route_payload`, `complete_route_step_for_distributor`, `save_leader_route_step`, `verify_user_access`, `validate_invitation_action` |

Los tres se reexportan desde `services/__init__.py`.

### Utilidades (`utils.py`)

| Función | Propósito |
|---|---|
| `get_first_leader_user()` | Resuelve `FIRST_LEADER_PRO` por username único |
| `build_scheduled_task_ranges(user, local_now, tz)` | Querysets de `ScheduledTask` de hoy / pasado / semana / mes |
| `build_month_calendar(...)` | Estructura de calendario mensual para el dashboard |
| `build_incentive_context(user, today, local_now)` | Contexto completo de incentivos, libre de N+1 |
| `build_downgrade_alerts(user)` | Alertas de degradación para el dashboard |
| `get_descendants_tree_optimized(user, max_depth)` | Árbol de descendientes BFS en una sola consulta masiva |
| `get_all_descendants_ids_with_generation(user, max_depth)` | Recorrido BFS de IDs con números de generación |
| `get_inactive_users_optimized(user, days)` | Descendientes inactivos; caché Redis, 5 min |
| `get_user_training_data_cached(user_id)` | Estadísticas de formación; caché Redis, 10 min |
| `get_user_answers_cached(user_id)` | Campos de formación respondidos; caché Redis, 10 min |
| `invalidate_user_cache` / `invalidate_ancestors_cache` | Invalidación de caché, en cascada hacia arriba por la cadena de patrocinio |
| `get_direct_children_with_data(user, generation)` | Hijos más recuento de nietos en dos consultas |
| `get_route_step(user)` | Pasos de ruta; copia desde el líder más cercano para líderes simples |

### Otros módulos

`birthdays.py` (detección de cumpleaños con caché Redis), `scheduled_task_reminders.py` y
`tasks.py` — tareas Celery para entrega push FCM, avisos de cumpleaños y recordatorios de tareas
programadas.

## Vistas e integración frontend

**Esta app usa HTMX**: de forma parcial en el dashboard y de forma extensiva en la sección Mi
Equipo, donde sustituyó el anterior `my-team.js` monolítico.

Prefijo de URL: **`/main/`**

### Endpoints HTMX

| Endpoint | Name | Devuelve |
|---|---|---|
| `home/` (POST) | `home` | `components/card-sh-tasks.html` tras completar una tarea programada |
| `set-monthly-goals/`, `save-monthly-stats/` | `set_monthly_goals`, `save_monthly_stats` | `components/monthly-stats-htmx.html` cuando `request.htmx` (sección más resúmenes OOB de los modales) |
| `load-incentive-form/` | `load_incentive_form` | `components/partials/incentive-form-fields.html` |
| `my-team/` (POST) | `my_team` | Árbol de invitaciones re-renderizado tras enviar una invitación |
| `load-user-children/` | `load_user_children` | Rama del árbol cargada de forma diferida |
| `load-user-training-data/` | `load_user_training_data` | Fragmento del modal de estadísticas de formación |
| `load-user-answers/` | `load_user_answers` | Fragmento del modal de campos respondidos |
| `delete-pending-invitation/`, `resend-invitation/` | `delete_pending_invitation`, `resend_invitation` | Fila de invitación / celda de acciones actualizada |

Plantillas participantes: `home.html` con `modal-confirm-complete.html`, `modal-add-new.html` y
`base-modal.html`; `modal-incentive.html` impulsado por el global `static/js/htmx_modal_form.js`; y
en Mi Equipo, `modal-new-user.html`, `modal-delete-invitation.html`,
`modal-resend-invitation.html`, `invited-users-tree-lazy.html`,
`invited-user-actions-cell.html`. Los modales llevan `data-close-modal`.

### Endpoints HTML y JSON

| URL | Name | Descripción |
|---|---|---|
| `home/` | `home` | Dashboard: tareas programadas, incentivos, calendario, retos |
| `my-team/` | `my_team` | Árbol de equipo, invitaciones, pasos de ruta |
| `personal-info/` | `personal_info` | Formulario de perfil |
| `save-incentive/` · `delete-incentive/` | `save_incentive`, `delete_incentive` | CRUD de incentivos con adjuntos |
| `save-type-incentive/` | `save_type_incentive` | Gestión de categorías, restringida a `USER_ROOT` |
| `save-favorite-incentive/` | `save_favorite_incentive` | Alternar favorito (JSON) |
| `create-incentive-task/` · `get-incentive-month-tasks/` | `create_incentive_task`, `get_incentive_month_tasks` | Tareas mensuales de incentivo (JSON) |
| `copy/<id>/` | `copy_incentive` | Copia un incentivo visible a la cuenta del usuario |
| `register-push-subscription/` | `register_push_subscription` | Guarda el token FCM (JSON). Devuelve 401 JSON si el usuario no está autenticado; `@require_POST`; **la protección CSRF está activa** |
| `set-notifications-activated/` | `set_notifications_activated` | Alterna el opt-in de notificaciones |
| `notifications/` · `notification-redirect/` | `all_notifications`, `notification_redirect` | Centro de notificaciones y redirección de marcado como leído |
| `save-route-step/` · `delete-route-step/` | `save_route_step`, `delete_route_step` | CRUD de pasos de ruta del líder (JSON o redirección según la cabecera AJAX) |
| `load-distributor-route/` · `complete-distributor-route-step/` | `load_distributor_route`, `complete_distributor_route_step` | Payload de ruta del distribuidor y compleción (JSON) |

Las librerías del dashboard bajo el pliegue (Leaflet, el geocoder, ApexCharts) se cargan de forma
diferida; jQuery y Bootstrap están autoalojados y se cargan al final de `<body>`.

### Lógica de acceso

- Toda vista exige autenticación, forzada por `LoginRequiredMiddleware`.
- `save_type_incentive` está restringida a `USER_ROOT`.
- El CRUD de incentivos se valida con `check_action_allowed(user, INCENTIVE_MODEL_KEY, …)`.
- Las escrituras de pasos de ruta exigen `is_any_leader()`.
- Los endpoints de datos de equipo llaman a `verify_user_access`, que recorre la cadena de
  patrocinio hasta profundidad 100.
- Solo el patrocinador directo puede borrar o reenviar una invitación pendiente.

## Configuración y dependencias

| Setting | Propósito |
|---|---|
| `FIREBASE_CREDENTIALS_JSON`, `FIREBASE_WEB_*`, `FIREBASE_WEB_VAPID_KEY` | Registro de suscripción push y entrega FCM desde `tasks.py` |
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Cachés de equipo, formación, cumpleaños e inactividad |
| `R2_*` / `STORAGES` | Imágenes de fondo y adjuntos de incentivos |
| Ajustes de email (SMTP) | Emails de invitación y recordatorio |
| `USER_ROOT`, `FIRST_LEADER_PRO` (desde `core.const`) | Identidades de arranque para acciones solo de admin |

Servicios externos: Redis, Celery (`tasks.py` para push FCM, cumpleaños, recordatorios programados),
Firebase Cloud Messaging y los CDN de Leaflet / ApexCharts en el dashboard. **Sin integración
directa con Sentry** — las excepciones se propagan al manejador global.

Dependencias de apps: `challenge` (`Task`, `UserTaskProgress`, `get_progress_challenge_user`),
`communication` (`ScheduledTask`, `Contact`, `ActivityContact`), `core`, `training` (`UserProgress`),
`user_levels`, `users`.
