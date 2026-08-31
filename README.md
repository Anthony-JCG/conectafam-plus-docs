# Conectafam Plus

Django 5.2 monolith powering **Conectafam Plus**, a network-marketing platform for distributors:
team management, training, challenges, CRM, boards, landing pages, live streams, and
subscription billing.

This file is the single entry point to the repository. Each app documents itself in its own
`README.md`; infrastructure lives under [`docs/`](docs/README.md).

---

## Stack


| Layer              | Implementation                                                                                           |
| ------------------ | -------------------------------------------------------------------------------------------------------- |
| Framework          | Django 5.2 (WSGI, Gunicorn + gevent)                                                                     |
| Database           | MySQL 8 (`utf8mb4`) in production, SQLite when `DEBUG=1`                                                 |
| Cache / broker     | Redis                                                                                                    |
| Async tasks        | Celery worker + Celery beat                                                                              |
| Reverse proxy      | Nginx (TLS, static files, HLS media)                                                                     |
| Edge / CDN         | Bunny.net in front of origin Nginx in production. Cloudflare's site proxy is not used                    |
| Frontend           | Server-rendered templates + vanilla JS, Bootstrap, jQuery. **HTMX for form submission in selected apps** |
| Media storage      | Cloudflare R2 (S3-compatible) in production                                                              |
| Observability      | Sentry                                                                                                   |
| Payments           | Stripe (Checkout + Customer Portal)                                                                      |
| Push notifications | Firebase Cloud Messaging / Web Push                                                                      |


---



## Architecture

The project is a single Django project (`Platform/`) with all business logic split into apps under
`apps/`. There are no service boundaries: apps import each other directly, and the dependency
direction is enforced by convention rather than tooling.

### The central axis: `users.User`

`users.User` is a custom user model with a **self-referential** `sponsor` **FK** that forms the MLM tree.
Every app with models attaches to it, and most cross-app behaviour — visibility, notifications,
shared content — is a traversal of that tree.

Propagation down the tree **stops at the first** `leader_pro` node. This single rule governs which
users see a leader's shared content, who receives a downline notification, and how far a downgrade
cascades.

### The two core apps

```
                    ┌──────────────────────────────┐
                    │  apps/core/                  │  no models
                    │  files, Redis, HTMX helpers, │  no business logic
                    │  push, constants, base forms │  imported by everyone
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  apps/user_levels/           │  permissions
                    │  levels, capabilities,       │  visibility
                    │  sponsor traversal, downgrade│  limits & routes
                    └──────────────┬───────────────┘
                                   │
   ┌───────────────┬───────────────┼───────────────┬───────────────┐
   │               │               │               │               │
 boards        challenge      communication      landing         main
 links          pricing         streaming       training      keyboard_api
                                   │
                    ┌──────────────▼───────────────┐
                    │  apps/users/  →  User        │  central model
                    │  sponsor tree, auth, gates   │
                    └──────────────────────────────┘
```

Two rules hold across the codebase:

1. **Permissions and visibility live only in** `user_levels`**.** Any listing of a shareable resource
  goes through `get_model_visible_queryset` (or a specific variant), never a bare
   `Model.objects.filter(user=request.user)`.
2. `core` **owns no domain.** Business apps import from it; it reaches back only through lazy imports
  inside functions.



### HTMX adoption

HTMX is the standard for **form submission**, replacing full-page reloads and hand-written
fetch + DOM code. It is deliberately not used for JSON APIs, chart data, map data, or autocomplete.

Adoption is progressive — an app gets HTMX during its scheduled refactor:


| Uses HTMX                                    | Does not use HTMX                                                                                        |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `boards`, `communication`, `landing`, `main` | `challenge`, `core`, `keyboard_api`, `links`, `pricing`, `streaming`, `training`, `users`, `user_levels` |


The shared contract is provided by `core.utils.htmx` (`attach_toast_trigger`, `htmx_error_response`)
and consumed on the client by the modal lifecycle in `static/js/core.js`. CSRF is handled by
`hx-headers` on `<body>` using the server-rendered token.

---



## Application index


| App                                             | URL prefix                     | HTMX | Purpose                                                                               |
| ----------------------------------------------- | ------------------------------ | ---- | ------------------------------------------------------------------------------------- |
| [`core`](apps/core/README.md)                   | —                              | —    | Cross-cutting infrastructure: media processing, Redis, push, HTMX helpers, base forms |
| [`user_levels`](apps/user_levels/README.md)     | —                              | —    | Permissions, capabilities, visibility, downgrade lifecycle                            |
| [`users`](apps/users/README.md)                 | `/`                            | No   | `User` model, sponsor tree, auth, multi-account, middleware stack                     |
| [`main`](apps/main/README.md)                   | `/main/`                       | Yes  | Dashboard, team management, incentives, distributor route, notifications              |
| [`training`](apps/training/README.md)           | `/training/`                   | No   | Categories, courses, formations, blocking onboarding                                  |
| [`challenge`](apps/challenge/README.md)         | `/challenges/`                 | No   | Challenges and recurring daily/monthly tasks                                          |
| [`communication`](apps/communication/README.md) | `/communication/`              | Yes  | CRM: contacts, follow-ups, message templates, WhatsApp links                          |
| [`boards`](apps/boards/README.md)               | `/boards/`                     | Yes  | Personal resource library with mosaic view, sharing, collaboration                    |
| [`landing`](apps/landing/README.md)             | `/landing-page/`, `/p/<slug>/` | Yes  | Block-based landing page builder and templates                                        |
| [`links`](apps/links/README.md)                 | `/links/`                      | No   | Link Mate — link-in-bio page                                                          |
| [`streaming`](apps/streaming/README.md)         | `/streaming/`                  | No   | Live sessions with HLS video and post-session conversion                              |
| [`pricing`](apps/pricing/README.md)             | `/pricing/`                    | No   | Stripe subscriptions, Customer Portal, webhooks, free trial cancellation              |
| [`keyboard_api`](apps/keyboard_api/README.md)   | `/api/keyboard/`               | n/a  | Token-authenticated JSON API for the mobile keyboard client                           |

A `—` prefix means the app owns no URLConf. `core` has no `urls.py`: its handful of views are
registered one by one at the site root in `Platform/urls.py` (`/sw.js`, `/share-preview/`,
`/update-drag-drop/`, …). `user_levels` has neither `urls.py` nor `views.py` — it is a pure
domain layer consumed by the other apps through its middleware and public functions.


---



## Infrastructure

The project is containerised across **three environments**, all defined by the same
`docker-compose.yml` plus environment-specific overrides:


| Environment       | Compose file                                                     | Web process          | Celery                                    |
| ----------------- | ---------------------------------------------------------------- | -------------------- | ----------------------------------------- |
| Local development | `docker-compose.dev.yml` (`DEBUG=1`)                             | `runserver`          | 1 container, concurrency 1                |
| Test              | `docker-compose.yml` (`NGINX_CONFIG=test`, `TEST_ENVIRONMENT=1`) | Gunicorn, 2 workers  | `--scale celery-worker=2`                 |
| Production        | `docker-compose.yml` (`NGINX_CONFIG=production`)                 | Gunicorn, 10 workers | `--scale celery-worker=5`, concurrency 10 |


Two data-deployment models are supported: **Model A** runs `db` and `redis` as containers (the target
architecture), while **Model B** (`docker-compose.host-services.yml`) keeps MySQL and Redis on the
host during migration from the legacy systemd deployment.

> Full reference — architecture diagram, Nginx configuration, entrypoint behaviour, volumes, CI/CD,
> and migration procedure: [`docs/docker.md`](docs/docker.md).
> Database backup and restore procedure: [`docs/backups.md`](docs/backups.md).



### Quick start

```powershell
copy .env.docker.example .env
docker compose -f docker-compose.dev.yml up --build
```

Without Docker, using the local virtual environment:

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver
```

---



## External services



### Sentry

Initialised in `Platform/settings.py` only when `SENTRY_DSN` is set. Integrations: Django, Celery,
Redis, and logging (`WARNING` as breadcrumbs, `ERROR` as events).

`send_default_pii` is off, `profiles_sample_rate` is `0`, `DisallowedHost` is ignored, and a
`before_send` hook drops the recurring "Cannot connect to redis / Connection refused" log noise.
`SENTRY_ENVIRONMENT` defaults to `development`, `test`, or `production` based on `DEBUG` and
`TEST_ENVIRONMENT`.

Application code reports to Sentry explicitly in one place: `core.utils.fcm_observability`, which
forwards FCM delivery anomalies.

### Bunny.net

Production TLS termination and caching sit on Bunny.net in front of origin Nginx. Cloudflare's
proxy is not used for the site: its anycast ranges are unreachable from some operator networks in
the user base. There is no Bunny configuration in this repository; the origin still speaks HTTP to
Nginx as documented in [`docs/docker.md`](docs/docker.md).

### Cloudflare R2

Object storage for media in production — not the site CDN. `apps/core/storage_config.py` gates
activation: R2 is used only when the environment is production, `TEST_ENVIRONMENT` is off, and all
four R2 credentials are present. `STORAGES["default"]` then becomes `S3Boto3Storage` with
`location="media"` and `querystring_auth=False`, and `MEDIA_URL` points at
`https://{R2_CUSTOM_DOMAIN}/media/`.

**Static files never go to R2.** They use `ManifestStaticFilesStorage`, are built by `collectstatic`
during the Docker image build, and are served by Nginx.

### Other integrations


| Service                  | Owner app                                                                                                   | Notes                                                           |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Stripe                   | `[pricing](apps/pricing/README.md)`                                                                         | Checkout, Customer Portal, 8 webhook events                     |
| Firebase Cloud Messaging | `[core](apps/core/README.md)`, `[main](apps/main/README.md)`, `[keyboard_api](apps/keyboard_api/README.md)` | Web Push and silent push for mobile sync                        |
| Redis                    | `[core](apps/core/README.md)`                                                                               | Cache, notification feed, processing locks, search index        |
| Celery                   | multiple                                                                                                    | Media transcoding, email, push, trial expiry, downgrade cleanup |
| ffmpeg                   | `[core](apps/core/README.md)`, `[boards](apps/boards/README.md)`, `[streaming](apps/streaming/README.md)`   | WebP/HLS conversion; bundled in the image                       |


---



## Configuration

All settings are read from the environment through `django-environ`; the template is
`.env.docker.example`.


| Group         | Variables                                                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Core          | `DEBUG`, `TEST_ENVIRONMENT`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS_EXTRA`, `DJANGO_CSRF_TRUSTED_ORIGINS_EXTRA`, `STATIC_VERSION` |
| Database      | `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`                                                                             |
| Redis         | `REDIS_URL`, `REDIS_KEY_PREFIX`, `USER_LEVEL_CACHE_TTL`                                                                               |
| Sentry        | `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_BROWSER_TRACES_SAMPLE_RATE`                                  |
| Cloudflare R2 | `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_CUSTOM_DOMAIN`                                   |
| Stripe        | `STRIPE_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`                                                                        |
| Firebase      | `FIREBASE_CREDENTIALS_JSON`, `FIREBASE_WEB_*`, `FIREBASE_WEB_VAPID_KEY`                                                               |
| Email         | `EMAIL_HOST_PASSWORD` (console backend when `DEBUG`)                                                                                  |
| Security      | `RECAPTCHA_PUBLIC_KEY`, `RECAPTCHA_PRIVATE_KEY`                                                                                       |
| Media         | `FFMPEG`, `FFPROBE`, `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE`                                                     |
| Runtime       | `GUNICORN_WORKERS`, `GUNICORN_BIND`, `CELERY_CONCURRENCY`, `NGINX_CONFIG`, `WEB_PORT`                                                 |




### Middleware

Custom middleware runs in this order, six from `users` and one from `user_levels`:

`TimezoneFromSessionMiddleware` → `AccountRegistryMiddleware` → `TwoFactorAuthMiddleware` →
`LoginRequiredMiddleware` → `InitialTrainingGateMiddleware` → `RouteLevelAccessMiddleware` →
`UpdateLastActivityMiddleware`, followed by `django_htmx.middleware.HtmxMiddleware`.

---



## Development


| Tool                   | Command                                                                                                        |
| ---------------------- | -------------------------------------------------------------------------------------------------------------- |
| Lint / format (Python) | `ruff check .` · `ruff format .` — configured in `pyproject.toml`, line length 120                             |
| Lint / format (JS)     | `biome check` — configured in `biome.json`                                                                     |
| Tests                  | `.venv\Scripts\pytest.exe apps/<app>/tests/ -v` — pytest + pytest-django + factory-boy, `testpaths = ["apps"]` |
| Pre-commit             | `.pre-commit-config.yaml` is the authority on automated fixes; do not revert its corrections                   |


Commit messages follow **Conventional Commits** (`<type>(<scope>): <description>`, first line ≤ 60
characters). Releases and `[CHANGELOG.md](CHANGELOG.md)` are generated by release-please.

### Public documentation mirror

Documentation lives in this repository and is mirrored to
[`conectafam-plus-docs`](https://github.com/Anthony-JCG/conectafam-plus-docs) when a push to
`main` includes changes to tracked `.md` files (excluding `.github/` and `.cursor/`). GitHub
Actions on that repository builds the MkDocs site.

Workflow: [`.github/workflows/sync-docs.yml`](.github/workflows/sync-docs.yml).

---



## Documentation index


| Document                                                 | Contents                                                                                         |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| [`docs/docker.md`](docs/docker.md)                       | Container architecture, three environments, Nginx, entrypoint, volumes, CI/CD, systemd migration |
| [`docs/backups.md`](docs/backups.md)                     | Database backup and restore                                                                      |
| [`docs/user-levels-cache.md`](docs/user-levels-cache.md) | Redis cache for `user_levels`: keys, TTL, invalidation, debugging                                |
| [`CHANGELOG.md`](CHANGELOG.md)                           | Release history                                                                                  |
| `apps/*/README.md`                                       | Per-app reference — see the [application index](#application-index)                              |


