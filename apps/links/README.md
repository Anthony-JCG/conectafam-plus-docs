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
- **`core`** — `BaseForm` and admin registration helpers.

## Models and Data

| Model | Relationships |
|---|---|
| `LinkMate` | OneToOne → `users.User`. Root container: display name, bio, avatar, store link |
| `LinkMateCustomization` | OneToOne → `LinkMate`; FK → `PredefinedBackground` — font, colours, background |
| `LinkMateProCustomization` | OneToOne → `LinkMate` — PRO layout, including `get_embed_video_url()` for YouTube |
| `PersonalLink` | FK → `LinkMate` — ordered custom links |
| `SocialMedia` | Catalogue of supported networks; no user FK |
| `SocialMediaLinkMate` | FK → `LinkMate`; FK → `SocialMedia` — the user's social links |

There is no `services.py` or `utils.py`; logic lives in `views.py`, `forms.py`, and the static JS.
Ordering is persisted through dedicated reorder endpoints.

## Views and Frontend Integration

**This app does not use HTMX.** Editing is a mix of standard form posts that redirect and AJAX
endpoints returning `JsonResponse`; no view returns an HTML fragment.

URL prefix: **`/links/`**. The public page lives outside this app, at `<username>_link/`
(`users.views.personal_link_mate`).

| URL | View | Response |
|---|---|---|
| `link-mate` | `link_mate` | Editing panel (HTML); visibility toggles answer JSON |
| `save-link/<link_mate_id>` · `save-pro-link/<link_mate_id>` | `save_link`, `save_pro_link` | Personal link CRUD (redirect) |
| `save-link-mate-pro/` | `save_link_mate_pro` | PRO customisation (redirect) |
| `save-social-media-link/` | `save_social_media_link` | Social link CRUD (redirect) |
| `delete-link/` | `delete_link` | Deletes a personal or social link (redirect) |
| `save-store-link/` | `save_store_link` | Store URL (redirect) |
| `save-link-mate/` | `save_link_mate` | Basic Link Mate data (JSON) |
| `save-customization/` | `save_link_mate_customization` | Font, colour, background (JSON) |
| `reorder-items/` · `reorder-pro-items/` · `reorder-social-media-items/` | `reorder_items`, `reorder_pro_items`, `reorder_social_media_items` | Drag-and-drop ordering (JSON) |

## Configuration and Dependencies

| Setting | Purpose |
|---|---|
| `R2_*` / `STORAGES` | Avatars and background images through the global media backend |
| `LIMIT_USER_LINKS` (from `core.const`) | Cap on personal links per user |
| `RESTRICTED_ALERT_LINK_APPEARANCE` (from `user_levels.const`) | Copy for the appearance upgrade modal |

The only external integration is YouTube embedding in `LinkMateProCustomization`. **No Sentry,
Redis, Celery, or Stripe usage.**

App dependencies: `core`, `user_levels` (constant only), and `users` for the public route.
