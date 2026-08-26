# landing

## Description

Block-based landing page builder. Users compose public capture pages from ordered blocks (hero,
text, video, PDF, carousel, FAQ, learning list, CTA, contact form) and publish them either under a
long URL or a short "pretty" slug. Leaders can share a landing as a **template** that downline users
fork into their own copy.

The same engine backs `boards`: a `page`-type board item creates a `LandingPage` with
`page_context=board`, rendered through `services/board_editor.py`.

Relationship to the core apps:

- **`user_levels`** — creation limits and PRO gating enter through
  `services/landing_permissions.py` (`check_landing_create_allowed`,
  `assert_blank_landing_create_allowed`); `RESTRICTED_ALERT_*` constants drive the upgrade modals.
- **`core`** — `BaseForm`, file processing, Quill payload normalisation, PDF thumbnails, and the
  `attach_toast_trigger` / `htmx_error_response` HTMX contract.
- **`users.User`** — owns `LandingPage` and `LandingPageUserTemplateState`.
- **`communication`** — landing blocks and CTAs point at `WhatsAppLink`; submitted contact forms
  create `Contact` rows.
- **`boards`** — blocks can be imported from `BoardItem`, and a board page is a landing.

## Models and Data

| Model | Relationships |
|---|---|
| `LandingPage` | FK → `users.User`; FK → `self` (`source_landing`, the template it was forked from) |
| `LandingPageBlock` | FK → `LandingPage`; optional FK → `boards.BoardItem`; FK → `communication.WhatsAppLink` |
| `LandingPageLearningItem` | FK → `LandingPageBlock` |
| `LandingPageFaqItem` | FK → `LandingPageBlock` |
| `LandingPageCarouselItemBlock` | FK → `LandingPageBlock` |
| `LandingPageCustomization` | OneToOne → `LandingPage` — theme, colours, typography |
| `LandingPageUserTemplateState` | FK → `users.User`; FK → `LandingPage` (`template`); OneToOne → `LandingPage` for `share_landing` and `fork_landing`; FK → `communication.WhatsAppLink` (`default_whatsapp_link`) |
| `LandingPageBuilder` | OneToOne → `LandingPage`. GrapesJS payload; **no views expose it yet** |

Page content is entirely block-driven: there are no per-section boolean flags on `LandingPage`.
Ordering, visibility, and block type live on `LandingPageBlock`.

PDF blocks store a `document_thumbnail` generated server-side by `services/document_preview.py`
(reusing `core.utils.pdf_preview`), so the public page renders an image instead of booting PDF.js.

### Services

| Module | Responsibility |
|---|---|
| `services/landing_permissions.py` | Creation permissions, share/fork, deep copy, listing querysets |
| `services/landing_blocks.py` | Persistence of blocks and nested items |
| `services/landing_serialize.py` | JSON serialisation and table rows |
| `services/landing_preview.py` | Preview rendering inside a savepoint + rollback |
| `services/landing_slugs.py` | `public_slug` generation for pretty URLs |
| `services/document_preview.py` | WebP thumbnail sync for PDF blocks |
| `services/board_editor.py` | Board-page integration and `BoardItem` import |
| `utils.py` | Block summaries, session unlocking, AJAX/WhatsApp helpers, form merging |

## Views and Frontend Integration

**This app uses HTMX** for the landing dashboard and for block manipulation inside the content
editor.

URL prefix: **`/landing-page/`**. Pretty URLs are mounted separately in `Platform/urls.py` as
`p/<slug>/` → `landing_pretty`.

### HTMX endpoints

| Endpoint | Name | HTMX behaviour |
|---|---|---|
| `load-basic-form/` | `load_landing_basic_form` | GET partial with the basic-data form; requested via `htmx.ajax` from `landing-page.html` |
| `save/` | `save_landing_page` | HTMX branch returns a partial + `HX-Trigger` toast; non-HTMX callers still receive JSON |
| `delete/` | `delete_landing_page` | Partial + `HX-Trigger` toast |
| `toggle-pretty-url/` | `toggle_landing_pretty_url` | Re-renders the landings table |
| `edit/<id>/add-block/` | `add_landing_block` | Appends a block row fragment |
| `edit/<id>/add-nested-item/` | `add_landing_nested_item` | Appends a nested item row (carousel, FAQ, learning) |
| `edit/<id>/import-board-items/` | `import_board_items_to_landing` | Injects blocks built from selected `BoardItem`s |
| `block/delete/` | `delete_landing_block` | Removes a block, `HX-Trigger` toast |

Validation errors return `htmx_error_response` (422). Submitting templates:
`components/modal-landing-basic.html` and `components/modal-delete-landing.html` (both with
`data-close-modal`) and `components/table-landings.html`. Inside the editor, requests are issued
programmatically with `htmx.ajax` from `static/js/landing_blocks.js` and
`static/js/landing_board_picker.js`.

### HTML and JSON endpoints

| Route | Name | Response |
|---|---|---|
| `<username>/<type_contact>_<landing_id>/` | `landing_template` | Public landing; POST captures a contact |
| `p/<slug>/` (root-mounted) | `landing_pretty` | Same view behind the short slug |
| `""` | `landing_page` | Authenticated dashboard listing the user's landings |
| `edit/<id>/` | `edit_landing_content` | Block editor |
| `edit/<id>/preview/` | `preview_landing_content` | POST → rendered HTML preview (savepoint + rollback) |
| `share-template/` | `share_leader_landing` | JSON — publishes a leader template |
| `duplicate-template/` | `duplicate_landing_template` | JSON — forks a template into the user's account |

Frontend modules in `static/js/`: `landing_blocks.js` (block manager and nested items),
`landing_ajax.js` (save pipeline and carousel preview sync), `landing_content_editor.js` (editor
orchestration, refreshes from the database after each save), `landing_board_picker.js`,
`landing_pdf_block.js` (lazy PDF.js fallback via `IntersectionObserver`, only when no server-side
thumbnail exists). Public styles in `static/css/landing-page.css`.

## Configuration and Dependencies

| Setting | Purpose |
|---|---|
| `R2_*` / `STORAGES` | Block images, videos, and PDFs are stored through the global media backend (Cloudflare R2 in production) |
| `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE` | Block file uploads |
| Email (SMTP) settings | Contact-capture notifications sent through `apps.users.utils.send_email` |

External integrations: YouTube (nocookie embeds and `i.ytimg.com` thumbnails), WhatsApp deep links,
and an optional **Facebook Pixel** per landing (`facebook_pixel_id`).

This app has **no direct Sentry, Redis, or Celery usage**; media storage is inherited from the global
configuration described in [`apps/core/README.md`](../core/README.md) and
[`docs/docker.md`](../../docs/docker.md).

App dependencies: `core`, `users`, `user_levels`, `communication`, `boards`, `links`.
