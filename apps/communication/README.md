# communication

## Description

CRM for the distributor's network: contacts, follow-up scheduling, activity history, reusable
message templates, and WhatsApp deep links. It is the app a user works in daily to track prospects
from first contact through membership.

Relationship to the core apps:

- **`users.User`** — owns `Contact`, `PredefinedMessage`, `ContactMembershipStatus`, `WhatsAppLink`,
  and message customisations. The relationship is bidirectional: `users.User.contact` is a OneToOne
  back into `Contact`, so a user who registered from a contact keeps both rows in sync.
- **`user_levels`** — every create/delete path calls `check_action_allowed`,
  `check_scheduled_task_creation_allowed`, or `check_activity_contact_creation_allowed`; downgraded
  users are filtered through `collect_downgrade_blocks`.
- **`core`** — `BaseForm`, custom widgets, image processing, and the HTMX response helpers.

`WhatsAppLink` is consumed by other apps as a shared building block: `landing` blocks and CTAs and
`streaming` post-finalisation pages both point at it.

## Models and Data

| Model | Relationships |
|---|---|
| `Contact` | FK → `users.User`; M2M → `ContactLabel` |
| `ContactLabel` | Tag catalogue; no user FK |
| `ScheduledTask` | FK → `Contact`; FK → `PredefinedMessage` (`action_message`) |
| `ActivityContact` | FK → `Contact` — append-only interaction history |
| `PredefinedMessage` | FK → `users.User`; FK → `self` (`root_message`, follow-up chains) |
| `FollowUpContactMessageCustomization` | FK → `users.User`; FK → `Contact`; FK → `PredefinedMessage` (`base_message`); OneToOne → `PredefinedMessage` (`personalized_message`) |
| `ContactMembershipStatus` | FK → `users.User` — user-defined pipeline stages |
| `WhatsAppLink` | FK → `users.User` — named `wa.me` deep links |

`ScheduledTask` and `WhatsAppLink` build `wa.me` URLs directly in the model; there is no WhatsApp
API client.

### Services and utilities

| Module | Responsibility |
|---|---|
| `services.py` | Persistence for scheduled tasks, activities, contacts, and predefined/follow-up messages; contact photo reprocessing |
| `utils.py` | Contact filtering and ordering, serialisation, HTMX partial rendering, membership-status policy, permission helpers |
| `const.py` | Session keys, pagination size, membership-status limits |

`signals.py` is registered from `apps.py`.

## Views and Frontend Integration

**This app uses HTMX** for contact detail tabs, contact/task/activity forms, and their result
fragments.

URL prefix: **`/communication/`**

### HTMX endpoints

| Endpoint | Name | HTMX behaviour |
|---|---|---|
| `contacts/` (POST) | `contacts` | Scheduled-task and activity submissions return `components/partials/tasks-list.html` or `activities-list.html`, plus an `HX-Trigger` toast |
| `load-contact-detail/` | `load_contact_detail` | Under HTMX, returns the `tareas` or `actividades` tab partial; without HTMX, returns JSON |
| `load-contact-form/` | `load_contact_form` | GET partial → `contact-form-pane.html` |
| `load-message-form/` | `load_message_form` | GET partial → `message-form-fields.html` / `follow-up-form-fields.html` |
| `load-whatsapp-link-form/` | `load_whatsapp_link_form` | GET partial → `whatsapp-link-form-fields.html` |

Submitting templates: `components/modals/modal-contact.html` (`hx-get` + `hx-target`),
`modal-sh-task.html` and `modal-activity-contact.html` (`hx-post` + `hx-target` + `data-close-modal`).
The message and WhatsApp-link modals in `messages.html` are driven by the global
`htmx_modal_form.js` loader rather than inline `hx-*` attributes.

### JSON and HTML endpoints

| Route | Name | Response |
|---|---|---|
| `contacts/` | `contacts` | Main contacts page (HTML) |
| `predefined-messages/` | `predefined_messages` | Message templates, follow-ups, and WhatsApp links (HTML) |
| `save-whatsapp-link/` | `save_whatsapp_link` | Saves a WhatsApp link |
| `delete-communication/` | `delete_communication` | Deletes a message, contact, or link |
| `load-contacts-page/` | `load_contacts_page` | Infinite-scroll pagination (HTML embedded in JSON) |
| `search-contacts/` | `search_contacts` | Contact search (JSON) |
| `simply-new-contact/` | `simply_new_contact` | Simplified contact creation |
| `import-contact/` | `import_contact` | Bulk JSON import |
| `membership-status/save/` · `<pk>/save/` · `<pk>/delete/` · `<pk>/toggle/` | `save_membership_status`, `save_membership_status_pk`, `delete_membership_status`, `toggle_membership_status` | Pipeline stage CRUD (JSON) |

## Configuration and Dependencies

This app requires **no dedicated settings**. It inherits the global media backend for contact photos
(Cloudflare R2 in production, configured by `core.storage_config`) and the standard upload limits.

| Setting | Purpose |
|---|---|
| `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE` | Contact photo and import payload sizes |
| `R2_*` / `STORAGES` | Contact photo storage through the global backend |

App dependencies: `core` (forms, widgets, constants), `main` (`InvitationUsuarioForm`),
`user_levels` (permissions, limits, downgrade blocks).

**No Sentry, Redis, Celery, or external API integration** lives in this app; WhatsApp interaction is
limited to generating `wa.me` URLs.
