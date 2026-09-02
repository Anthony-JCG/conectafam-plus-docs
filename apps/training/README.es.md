# training

## Descripción

Sistema de formación y onboarding. El contenido se organiza en tres niveles — **categoría → sección
(curso) → subsección (formación)** — y se divide en dos modos: `first_steps`, la ruta de onboarding
obligatoria, y `my_resources`, la biblioteca de formación propia del líder.

La app impone un gate duro sobre el resto de la plataforma: hasta que el usuario complete la
formación inicial, `users.middle.InitialTrainingGateMiddleware` redirige cada petición a
`/training/onboarding/`. Completarla también es lo que activa la prueba gratuita gestionada por
`user_levels`.

Relación con las apps núcleo:

- **`user_levels`** — visibilidad del contenido, gating por nivel (`visible_from` usa `LevelType`
  como choices, no una FK), permisos de creación y manejo de degradaciones.
- **`core`** — constantes (`FIRST_STEPS_TRAINING`, `MY_RESOURCES_TRAINING`), payloads Quill, caché
  Redis, notificaciones y utilidades de archivos.
- **`users.User`** — propietario de categorías, subsecciones autoradas, progreso y mensajes.

La visibilidad de `first_steps` tiene su propia regla de corte de línea
(`get_first_steps_visible_queryset`, `get_first_steps_top_sponsor`) superpuesta al recorrido estándar de
sponsor. La línea cortada sustituye las categorías de `USER_ROOT` / `FIRST_LEADER_PRO` por las del
usuario ancla, para que los líderes anidados sigan heredando ese contenido.

## Modelos y datos

| Modelo | Relaciones |
|---|---|
| `CategoryTraining` | FK → `users.User`. Nivel superior; `visible_from` lo restringe por nivel |
| `Section` | FK → `CategoryTraining` — un curso |
| `Subsection` | FK → `Section`; FK → `users.User` (nullable, autor) — una formación |
| `CategoryTrainingAccess` | FK → `CategoryTraining`; FK → `users.User` — concesiones explícitas para categorías ocultas |
| `SubsectionFile` | FK → `Subsection` — adjuntos |
| `InputFieldSubsection` | FK → `Subsection` — preguntas renderizadas dentro de una formación |
| `UserProgress` | FK → `users.User`; FK → `Subsection` — seguimiento de completado |
| `UserProgressAnswer` | FK → `UserProgress`; FK → `InputFieldSubsection` — respuestas enviadas |
| `TrainingMessages` | FK → `users.User` — mensajes de inicio/fin mostrados alrededor de una formación |
| `TrainingUserMessages` | FK → `users.User`; FK → `TrainingMessages` — estado de entrega por usuario |

### Utilidades

No hay `services.py`. La lógica vive en:

| Módulo | Responsabilidad |
|---|---|
| `utils.py` | Visibilidad de first-steps (`get_first_steps_visible_queryset`, `get_first_steps_top_sponsor`, `get_onboarding_categories`), agregación de progreso (`build_first_steps_progress_data`), completado de onboarding (`evaluate_initial_training_completion`), resolución de la primera subsección efectiva, emails de notificación al sponsor, manejo de mensajes de inicio/fin |
| `forms.py` | Formularios de categoría, sección, subsección, mensajes y primera formación |
| `signals.py` | Crea una categoría por defecto cuando se crea un `leader_pro`; invalida cachés de progreso y de acceso oculto. Registrado desde `apps.py` |

## Vistas e integración frontend

**Esta app no usa HTMX.** Su comportamiento dinámico es fetch/AJAX que devuelve `JsonResponse`, a
menudo con HTML prerenderizado dentro de una clave `html`.

> `templates/components/modal-confirm-complete.html` contiene un atributo `hx-post` condicional,
> pero cada `include` (`initial-training.html`, `training-course-formations.html`) pasa
> `no_reload="1"` sin `hx_post`, así que la rama HTMX nunca se emite. Es markup muerto.

Prefijo de URL: **`/training/`**

| URL | Vista | Respuesta |
|---|---|---|
| `mode/<training_mode>/` | `initial_training` | Listado de categorías del modo (HTML); POST marca progreso y devuelve JSON bajo AJAX |
| `mode/<training_mode>/course/<section_id>/` | `training_course_formations` | Detalle del curso con sus formaciones (HTML) |
| `onboarding/` | `onboarding` | Flujo bloqueante de formación inicial (HTML) |
| `global-search/` | `global_training_search` | Búsqueda en categorías, cursos y formaciones visibles (JSON) |
| `load_category_content/<id>/` | `load_category_content` | Carga diferida de los cursos de una categoría (JSON + HTML) |
| `load_section_content/<id>/` | `load_section_content` | Carga diferida de las formaciones de un curso (JSON + HTML) |
| `load_subsection_item/<id>/` | `load_subsection_item` | Refresca una formación individual (JSON + HTML) |
| `submit_subsection_answers/` | `submit_subsection_answers` | Guarda respuestas y marca completado (JSON) |
| `upload_subsection_file/` · `delete_subsection_file/` | `upload_subsection_file`, `delete_subsection_file` | CRUD de adjuntos (JSON) |
| `save_category/` · `save_section/` · `save_subsection/` | `save_category`, `save_section`, `save_subsection` | CRUD de autoría para líderes (JSON) |
| `save_input_field/` · `delete_input_field/` | `save_input_field`, `delete_input_field` | CRUD de preguntas (JSON) |
| `hidden_category_access/<id>/` · `save_hidden_category_access/` | `get_hidden_category_access`, `save_hidden_category_access` | Gestión de acceso a categorías ocultas (JSON) |
| `save_first_formation/` | `save_first_formation` | Guarda la primera formación personalizada del líder (redirect) |
| `save-training-messages/` | `save_training_messages` | Configuración de mensajes de inicio/fin (redirect) |
| `delete_element/` | `delete_element` | Borra una categoría, curso o formación propios (JSON) |
| `update_order/` | `update_order` | Reordenación drag-and-drop (JSON) |

## Configuración y dependencias

| Setting | Propósito |
|---|---|
| `FIRST_STEPS_TRAINING`, `MY_RESOURCES_TRAINING` (de `core.const`) | Identificadores de modo usados en URLs y consultas |
| `FIRST_STEPS_LINE_CUT_USERNAME` (de `core.const`) | Usuario ancla del corte de visibilidad de first-steps |
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Cachés de progreso y acceso oculto, invalidadas por signals |
| `R2_*` / `STORAGES` | Adjuntos e imágenes de formaciones mediante el backend global de media |
| Ajustes de email (SMTP) | Notificaciones al sponsor cuando un usuario de la línea descendente completa la formación |

Dependencias de la app: `core`, `users`, `user_levels`, `main` (notificaciones e invalidación de
caché de descendientes).

**Sin integración directa con Sentry, Celery ni Stripe.** La prueba gratuita que arranca al
completar la formación la posee `user_levels`; ver [`apps/pricing/README.es.md`](../pricing/README.es.md)
para cómo interactúa con la facturación.
