# links

## Description

"Link Mate": a per-user link-in-bio page. Each user gets one `LinkMate` with personal links, social
media links, an optional store link, and visual customisation. PRO users unlock an extended layout
with its own set of links and an embedded video.

Relationship to the core apps:

- **`users.User`** — OneToOne with `LinkMate`; the public page is served by `users.views.personal_link_mate`
  at `<username>_link/`, not by this app.
- **`user_levels`** — this app is the exception to the usual pattern: it does **not** call
  `check_action_allowed` or any visibility helper. It only imports `RESTRICTED_ALERT_LINK_APPEARANCE`
  from `user_levels.const` to render the upgrade modal in the template. Level gating for the PRO
  layout is presentational.
- **`core`** — `BaseForm`, HTMX response helpers (`attach_toast_trigger`, `htmx_error_response`),
  the generic `update_drag_drop` reordering endpoint, and admin registration helpers.

## Models and Data

| Model | Relationships |
|---|---|
| `LinkMate` | OneToOne → `users.User`. Root container: display name, bio, avatar, store link |
| `LinkMateCustomization` | OneToOne → `LinkMate`; FK → `PredefinedBackground` — font, colours, background |
| `LinkMateProCustomization` | OneToOne → `LinkMate` — PRO layout, including `get_embed_video_url()` for YouTube |
| `PersonalLink` | FK → `LinkMate` — ordered custom links; `is_pro` splits the standard and PRO lists |
| `SocialMedia` | Catalogue of supported networks; no user FK |
| `SocialMediaLinkMate` | FK → `LinkMate`; FK → `SocialMedia` — the user's social links |

The contact button has no row of its own: it shares the ordering scale of the personal links and its
position is stored in `LinkMate.order_contact_me`.

## Modules

| Module | Responsibility |
|---|---|
| `services.py` | Persistence: toggles, link/social/pro-customisation saves, deletes, personal-links reordering |
| `utils.py` | Context builders (`build_link_mate_context`, `build_ordered_items`) and HTMX partial rendering |
| `const.py` | Item-type keys and the `linkMatePreviewRefresh` client event name |
| `forms.py` | Model forms; `LinkMateCustomizationForm` validates one appearance field per request |

Every mutation is scoped to `request.user`'s `LinkMate`; views never trust an id coming from the
client on its own.

## Views and Frontend Integration

**This app uses HTMX** for every mutation. Forms and controls post through `hx-post`; the views
answer with the affected list partial (or `204`) plus an `HX-Trigger` carrying the success toast and
`linkMatePreviewRefresh`. Validation errors come back as `422` from `htmx_error_response`, which the
global handler in `core.js` turns into an error toast while leaving the modal open.

URL prefix: **`/links/`**. The public page lives outside this app, at `<username>_link/`
(`users.views.personal_link_mate`).

| URL | View | HTMX behaviour |
|---|---|---|
| `link-mate` | `link_mate` | Editing panel (GET only) |
| `toggle-item/` | `toggle_link_item` | Visibility switches → `204` |
| `load-personal-link-form/` | `load_personal_link_form` | GET partial → `partials/personal-link-fields.html` (`?pro=1` for the PRO list) |
| `save-personal-link/` | `save_personal_link` | Returns `personal-links.html` or `pro-links.html` |
| `load-social-link-form/` | `load_social_link_form` | GET partial → `partials/social-link-fields.html` |
| `save-social-link/` | `save_social_link` | Returns `social-links.html` |
| `delete-link/` | `delete_link` | Returns the affected list and sets `HX-Retarget` |
| `save-store-link/` | `save_store_link` | Returns `personal-links.html` |
| `save-link-mate/` | `save_link_mate` | Silent autosave on blur → `204` |
| `save-link-mate-pro/` | `save_link_mate_pro` | PRO customisation → `204` |
| `save-customization/` | `save_link_mate_customization` | Re-renders the control group (font, shape, background) or `204` |
| `reorder-items/` | `reorder_items` | Personal-links order including the contact button → `204` |

The personal, social, and PRO editor lists share `components/partials/link-list-row.html` for the
row chrome (grip, wrapping title, delete, toggle). Callers pass the visible text as `title`
(`item.label` on mixed personal rows, `.name` on PRO and social).

Modals: `modal-link.html` (personal and PRO) is driven by the global `htmx_modal_form.js` loader;
`modal-social-link.html` and `modal-store-link.html` use inline `hx-get` / `hx-post`. The shared
`modal-delete-confirm.html` switches to HTMX when included with `delete_hx=1`.

### JavaScript

`static/js/link-mate.js` is the only script this app ships. It holds what HTMX cannot express
declaratively: the `<link-preview-frame>` custom element (lazy iframe, debounced reload on
`linkMatePreviewRefresh`), tab persistence, the SortableJS binding for the personal-links list, the
live colour preview, and the seeding of the delete and store-link modals.

Reordering of the PRO and social lists uses the platform-wide drag & drop system
(`static/js/sortable-list.js` → `update_drag_drop`), declared through `data-*` attributes only. The
personal list keeps its own endpoint because the contact button takes part in the ordering without
being a database row, which the generic endpoint cannot express — it updates one field on one model.
Its order still posts through `htmx.ajax`, so no request in this app reads the CSRF cookie.

## Configuration and Dependencies

| Setting | Purpose |
|---|---|
| `R2_*` / `STORAGES` | Avatars and background images through the global media backend |
| `FORMS_URLFIELD_ASSUME_HTTPS` | Lets users type a store URL without a scheme |
| `RESTRICTED_ALERT_LINK_APPEARANCE` (from `user_levels.const`) | Copy for the appearance upgrade modal |

The only external integration is YouTube embedding in `LinkMateProCustomization`. **No Sentry,
Redis, Celery, or Stripe usage.**

App dependencies: `core`, `user_levels` (constant only), and `users` for the public route.
