# communication

## Descripción

CRM de la red del distribuidor: contactos, programación de seguimientos, historial de actividad,
plantillas de mensajes reutilizables y deep links de WhatsApp. Es la app en la que el usuario
trabaja a diario para seguir a los prospectos desde el primer contacto hasta la membresía.

Relación con las apps núcleo:

- **`users.User`** — propietario de `Contact`, `PredefinedMessage`, `ContactMembershipStatus`,
  `WhatsAppLink` y las personalizaciones de mensaje. La relación es bidireccional:
  `users.User.contact` es un OneToOne de vuelta a `Contact`, de modo que un usuario registrado a
  partir de un contacto mantiene ambas filas sincronizadas.
- **`user_levels`** — toda ruta de creación/borrado llama a `check_action_allowed`,
  `check_scheduled_task_creation_allowed` o `check_activity_contact_creation_allowed`; los usuarios
  degradados se filtran con `collect_downgrade_blocks`.
- **`core`** — `BaseForm`, widgets personalizados, procesamiento de imágenes y los helpers de
  respuesta HTMX.

`WhatsAppLink` lo consumen otras apps como bloque compartido: los bloques y CTAs de `landing` y las
páginas post-finalización de `streaming` apuntan a él.

## Modelos y datos

| Modelo | Relaciones |
|---|---|
| `Contact` | FK → `users.User`; M2M → `ContactLabel` |
| `ContactLabel` | Catálogo de etiquetas; sin FK de usuario |
| `ScheduledTask` | FK → `Contact`; FK → `PredefinedMessage` (`action_message`) |
| `ActivityContact` | FK → `Contact` — historial de interacciones append-only |
| `PredefinedMessage` | FK → `users.User`; FK → `self` (`root_message`, cadenas de seguimiento) |
| `FollowUpContactMessageCustomization` | FK → `users.User`; FK → `Contact`; FK → `PredefinedMessage` (`base_message`); OneToOne → `PredefinedMessage` (`personalized_message`) |
| `ContactMembershipStatus` | FK → `users.User` — etapas de pipeline definidas por el usuario |
| `WhatsAppLink` | FK → `users.User` — deep links `wa.me` con nombre |

`ScheduledTask` y `WhatsAppLink` construyen las URLs `wa.me` directamente en el modelo; no hay
cliente de la API de WhatsApp.

### Servicios y utilidades

| Módulo | Responsabilidad |
|---|---|
| `services.py` | Persistencia de tareas programadas, actividades, contactos y mensajes predefinidos/de seguimiento; reprocesado de fotos de contacto |
| `utils.py` | Filtrado y ordenación de contactos, serialización, renderizado de parciales HTMX, política de estados de membresía, helpers de permisos |
| `const.py` | Claves de sesión, tamaño de paginación, límites de estados de membresía |

`signals.py` se registra desde `apps.py`.

## Vistas e integración frontend

**Esta app usa HTMX** para las pestañas de detalle de contacto, los formularios de
contacto/tarea/actividad y sus fragmentos de resultado.

Prefijo de URL: **`/communication/`**

### Endpoints HTMX

| Endpoint | Name | Comportamiento HTMX |
|---|---|---|
| `contacts/` (POST) | `contacts` | Los envíos de tarea programada y actividad devuelven `components/partials/tasks-list.html` o `activities-list.html`, más un toast `HX-Trigger` |
| `load-contact-detail/` | `load_contact_detail` | Bajo HTMX, devuelve el parcial de la pestaña `tareas` o `actividades`; sin HTMX, devuelve JSON |
| `load-contact-form/` | `load_contact_form` | GET parcial → `contact-form-pane.html` |
| `load-message-form/` | `load_message_form` | GET parcial → `message-form-fields.html` / `follow-up-form-fields.html` |
| `load-whatsapp-link-form/` | `load_whatsapp_link_form` | GET parcial → `whatsapp-link-form-fields.html` |

Plantillas de envío: `components/modals/modal-contact.html` (`hx-get` + `hx-target`),
`modal-sh-task.html` y `modal-activity-contact.html` (`hx-post` + `hx-target` + `data-close-modal`).
Los modales de mensaje y de enlace WhatsApp en `messages.html` los impulsa el cargador global
`htmx_modal_form.js` en lugar de atributos `hx-*` en línea.

### Endpoints JSON y HTML

| Ruta | Name | Respuesta |
|---|---|---|
| `contacts/` | `contacts` | Página principal de contactos (HTML) |
| `predefined-messages/` | `predefined_messages` | Plantillas de mensaje, seguimientos y enlaces WhatsApp (HTML) |
| `save-whatsapp-link/` | `save_whatsapp_link` | Guarda un enlace WhatsApp |
| `delete-communication/` | `delete_communication` | Borra un mensaje, contacto o enlace |
| `load-contacts-page/` | `load_contacts_page` | Paginación de scroll infinito (HTML embebido en JSON) |
| `search-contacts/` | `search_contacts` | Búsqueda de contactos (JSON) |
| `simply-new-contact/` | `simply_new_contact` | Creación simplificada de contacto |
| `import-contact/` | `import_contact` | Importación masiva JSON |
| `membership-status/save/` · `<pk>/save/` · `<pk>/delete/` · `<pk>/toggle/` | `save_membership_status`, `save_membership_status_pk`, `delete_membership_status`, `toggle_membership_status` | CRUD de etapas del pipeline (JSON) |

## Configuración y dependencias

Esta app **no requiere settings dedicados**. Hereda el backend global de media para las fotos de
contacto (Cloudflare R2 en producción, configurado por `core.storage_config`) y los límites
estándar de subida.

| Setting | Propósito |
|---|---|
| `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE` | Tamaños de foto de contacto y de payload de importación |
| `R2_*` / `STORAGES` | Almacenamiento de fotos de contacto mediante el backend global |

Dependencias de la app: `core` (formularios, widgets, constantes), `main` (`InvitationUsuarioForm`),
`user_levels` (permisos, límites, bloqueos por degradación).

**No hay integración con Sentry, Redis, Celery ni APIs externas** en esta app; la interacción con
WhatsApp se limita a generar URLs `wa.me`.
