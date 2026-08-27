# Conectafam Plus

Monolito Django 5.2 que impulsa **Conectafam Plus**, una plataforma de network marketing para
distribuidores: gestión de equipo, formaciones, retos, CRM, tableros, landing pages, directos en vivo
y facturación por suscripción.

Este archivo es el punto de entrada del repositorio. Cada app se documenta en su propio `README.md`;
la infraestructura está en [`docs/`](docs/README.es.md).

---

## Stack


| Capa               | Implementación                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| Framework          | Django 5.2 (WSGI, Gunicorn + gevent)                                                                          |
| Base de datos      | MySQL 8 (`utf8mb4`) en producción; SQLite cuando `DEBUG=1`                                                    |
| Caché / broker     | Redis                                                                                                         |
| Tareas asíncronas  | Celery worker + Celery beat                                                                                   |
| Proxy inverso      | Nginx (TLS, estáticos, media HLS)                                                                             |
| Frontend           | Plantillas en servidor + JS vanilla, Bootstrap, jQuery. **HTMX para envío de formularios en apps seleccionadas** |
| Almacenamiento     | Cloudflare R2 (compatible S3) en producción                                                                   |
| Observabilidad     | Sentry                                                                                                        |
| Pagos              | Stripe (Checkout + Customer Portal)                                                                           |
| Notificaciones push| Firebase Cloud Messaging / Web Push                                                                           |


---



## Arquitectura

El repositorio es un único proyecto Django (`Platform/`) con la lógica de negocio repartida en apps
bajo `apps/`. No hay fronteras de servicio: las apps se importan entre sí y la dirección de
dependencias se mantiene por convención, no por tooling.

### El eje central: `users.User`

`users.User` es un modelo de usuario personalizado con una **FK autorreferencial** `sponsor` que
forma el árbol MLM. Toda app con modelos se engancha a él, y la mayor parte del comportamiento
transversal — visibilidad, notificaciones, contenido compartido — es un recorrido de ese árbol.

La propagación hacia abajo **se corta en el primer** nodo `leader_pro`. Esa única regla define qué
usuarios ven el contenido compartido de un líder, quién recibe una notificación de línea descendente
y hasta dónde llega una degradación.

### Las dos apps núcleo

```
                    ┌──────────────────────────────┐
                    │  apps/core/                  │  sin modelos
                    │  files, Redis, HTMX helpers, │  sin lógica de negocio
                    │  push, constants, base forms │  importada por todas
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  apps/user_levels/           │  permisos
                    │  levels, capabilities,       │  visibilidad
                    │  sponsor traversal, downgrade│  límites y rutas
                    └──────────────┬───────────────┘
                                   │
   ┌───────────────┬───────────────┼───────────────┬───────────────┐
   │               │               │               │               │
 boards        challenge      communication      landing         main
 links          pricing         streaming       training      keyboard_api
                                   │
                    ┌──────────────▼───────────────┐
                    │  apps/users/  →  User        │  modelo central
                    │  sponsor tree, auth, gates   │
                    └──────────────────────────────┘
```

En todo el código rigen dos reglas:

1. **Permisos y visibilidad viven solo en** `user_levels`**.** Cualquier listado de un recurso
   compartible pasa por `get_model_visible_queryset` (o una variante específica), nunca por un
   `Model.objects.filter(user=request.user)` aislado.
2. `core` **no posee dominio.** Las apps de negocio importan desde ella; ella solo vuelve a
   llamarlas mediante imports perezosos dentro de funciones.



### Adopción de HTMX

HTMX es el estándar para el **envío de formularios**, en sustitución de recargas completas y del
código manual de fetch + DOM. A propósito no se usa en APIs JSON, datos de gráficos, mapas ni
autocompletado.

La adopción es progresiva: cada app recibe HTMX en su refactor programado:


| Usa HTMX                                     | No usa HTMX                                                                                              |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `boards`, `communication`, `landing`, `main` | `challenge`, `core`, `keyboard_api`, `links`, `pricing`, `streaming`, `training`, `users`, `user_levels` |


El contrato compartido lo aporta `core.utils.htmx` (`attach_toast_trigger`, `htmx_error_response`) y
en el cliente lo consume el ciclo de vida de modales en `static/js/core.js`. El CSRF se resuelve con
`hx-headers` en `<body>` usando el token renderizado en el servidor.

---



## Índice de aplicaciones


| App                                             | Prefijo URL                    | HTMX | Propósito                                                                                          |
| ----------------------------------------------- | ------------------------------ | ---- | -------------------------------------------------------------------------------------------------- |
| [`core`](apps/core/README.es.md)                   | —                              | —    | Infraestructura transversal: media, Redis, push, helpers HTMX, formularios base                    |
| [`user_levels`](apps/user_levels/README.es.md)     | —                              | —    | Permisos, capabilities, visibilidad, ciclo de degradación                                          |
| [`users`](apps/users/README.es.md)                 | `/`                            | No   | Modelo `User`, árbol de patrocinio, auth, multi-cuenta, pila de middleware                         |
| [`main`](apps/main/README.es.md)                   | `/main/`                       | Yes  | Dashboard, equipo, incentivos, ruta del distribuidor, notificaciones                                |
| [`training`](apps/training/README.es.md)           | `/training/`                   | No   | Categorías, cursos, formaciones, onboarding bloqueante                                             |
| [`challenge`](apps/challenge/README.es.md)         | `/challenges/`                 | No   | Retos y tareas recurrentes diarias/mensuales                                                       |
| [`communication`](apps/communication/README.es.md) | `/communication/`              | Yes  | CRM: contactos, seguimientos, plantillas de mensaje, enlaces de WhatsApp                           |
| [`boards`](apps/boards/README.es.md)               | `/boards/`                     | Yes  | Biblioteca personal de recursos con mosaico, compartición y colaboración                           |
| [`landing`](apps/landing/README.es.md)             | `/landing-page/`, `/p/<slug>/` | Yes  | Constructor de landing pages por bloques y plantillas                                              |
| [`links`](apps/links/README.es.md)                 | `/links/`                      | No   | Link Mate — página link-in-bio                                                                     |
| [`streaming`](apps/streaming/README.es.md)         | `/streaming/`                  | No   | Sesiones en vivo con vídeo HLS y conversión post-sesión                                            |
| [`pricing`](apps/pricing/README.es.md)             | `/pricing/`                    | No   | Suscripciones Stripe, Customer Portal, webhooks, cancelación de prueba gratuita                    |
| [`keyboard_api`](apps/keyboard_api/README.es.md)   | `/api/keyboard/`               | n/a  | API JSON autenticada por token para el cliente del teclado móvil                                   |

Un prefijo `—` indica que la app no posee URLConf. `core` no tiene `urls.py`: sus pocas vistas se
registran una a una en la raíz del sitio en `Platform/urls.py` (`/sw.js`, `/share-preview/`,
`/update-drag-drop/`, …). `user_levels` no tiene ni `urls.py` ni `views.py`: es una capa de dominio
pura que el resto de apps consume a través de su middleware y sus funciones públicas.


---



## Infraestructura

El proyecto está contenerizado en **tres entornos**, todos definidos por el mismo
`docker-compose.yml` más overrides específicos:


| Entorno             | Compose                                                          | Proceso web          | Celery                                    |
| ------------------- | ---------------------------------------------------------------- | -------------------- | ----------------------------------------- |
| Desarrollo local    | `docker-compose.dev.yml` (`DEBUG=1`)                             | `runserver`          | 1 contenedor, concurrencia 1              |
| Test                | `docker-compose.yml` (`NGINX_CONFIG=test`, `TEST_ENVIRONMENT=1`) | Gunicorn, 2 workers  | `--scale celery-worker=2`                 |
| Producción          | `docker-compose.yml` (`NGINX_CONFIG=production`)                 | Gunicorn, 10 workers | `--scale celery-worker=5`, concurrencia 10 |


Hay dos modelos de despliegue de datos: el **Modelo A** ejecuta `db` y `redis` como contenedores
(arquitectura objetivo), mientras que el **Modelo B** (`docker-compose.host-services.yml`) deja
MySQL y Redis en el host durante la migración desde el despliegue legado con systemd.

> Referencia completa — diagrama de arquitectura, configuración de Nginx, comportamiento del
> entrypoint, volúmenes, CI/CD y procedimiento de migración: [`docs/docker.es.md`](docs/docker.es.md).
> Procedimiento de backup y restauración de base de datos: [`docs/backups.es.md`](docs/backups.es.md).



### Arranque rápido

```powershell
copy .env.docker.example .env
docker compose -f docker-compose.dev.yml up --build
```

Sin Docker, con el entorno virtual local:

```powershell
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver
```

---



## Servicios externos



### Sentry

Se inicializa en `Platform/settings.py` solo cuando está definido `SENTRY_DSN`. Integraciones:
Django, Celery, Redis y logging (`WARNING` como breadcrumbs, `ERROR` como eventos).

`send_default_pii` está desactivado, `profiles_sample_rate` es `0`, se ignora `DisallowedHost` y un
hook `before_send` descarta el ruido recurrente de logs «Cannot connect to redis / Connection
refused». `SENTRY_ENVIRONMENT` toma por defecto `development`, `test` o `production` según `DEBUG` y
`TEST_ENVIRONMENT`.

El código de aplicación reporta a Sentry de forma explícita en un solo sitio:
`core.utils.fcm_observability`, que reenvía anomalías de entrega FCM.

### Cloudflare

Cloudflare aporta la CDN y el almacenamiento de objetos **R2** para media.
`apps/core/storage_config.py` condiciona la activación: R2 solo se usa en producción, con
`TEST_ENVIRONMENT` desactivado y las cuatro credenciales R2 presentes. Entonces
`STORAGES["default"]` pasa a `S3Boto3Storage` con `location="media"` y `querystring_auth=False`, y
`MEDIA_URL` apunta a `https://{R2_CUSTOM_DOMAIN}/media/`.

**Los estáticos nunca van a R2.** Usan `ManifestStaticFilesStorage`, se generan con `collectstatic`
durante el build de la imagen Docker y los sirve Nginx.

### Otras integraciones


| Servicio                 | App responsable                                                                                             | Notas                                                            |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Stripe                   | [`pricing`](apps/pricing/README.es.md)                                                                         | Checkout, Customer Portal, 8 eventos de webhook                  |
| Firebase Cloud Messaging | [`core`](apps/core/README.es.md), [`main`](apps/main/README.es.md), [`keyboard_api`](apps/keyboard_api/README.es.md) | Web Push y push silencioso para sync móvil                |
| Redis                    | [`core`](apps/core/README.es.md)                                                                               | Caché, feed de notificaciones, locks de procesamiento, índice de búsqueda |
| Celery                   | varias                                                                                                      | Transcodificación, email, push, fin de trial, limpieza de degradación |
| ffmpeg                   | [`core`](apps/core/README.es.md), [`boards`](apps/boards/README.es.md), [`streaming`](apps/streaming/README.es.md) | Conversión WebP/HLS; incluido en la imagen                   |


---



## Configuración

Todos los settings se leen del entorno mediante `django-environ`; la plantilla es
`.env.docker.example`.


| Grupo         | Variables                                                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Core          | `DEBUG`, `TEST_ENVIRONMENT`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS_EXTRA`, `DJANGO_CSRF_TRUSTED_ORIGINS_EXTRA`, `STATIC_VERSION` |
| Base de datos | `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`                                                                             |
| Redis         | `REDIS_URL`, `REDIS_KEY_PREFIX`, `USER_LEVEL_CACHE_TTL`                                                                               |
| Sentry        | `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_BROWSER_TRACES_SAMPLE_RATE`                                  |
| Cloudflare R2 | `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_CUSTOM_DOMAIN`                                   |
| Stripe        | `STRIPE_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`                                                                        |
| Firebase      | `FIREBASE_CREDENTIALS_JSON`, `FIREBASE_WEB_*`, `FIREBASE_WEB_VAPID_KEY`                                                               |
| Email         | `EMAIL_HOST_PASSWORD` (backend de consola cuando `DEBUG`)                                                                             |
| Seguridad     | `RECAPTCHA_PUBLIC_KEY`, `RECAPTCHA_PRIVATE_KEY`                                                                                       |
| Media         | `FFMPEG`, `FFPROBE`, `DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE`                                                     |
| Runtime       | `GUNICORN_WORKERS`, `GUNICORN_BIND`, `CELERY_CONCURRENCY`, `NGINX_CONFIG`, `WEB_PORT`                                                 |



### Middleware

El middleware propio corre en este orden, seis de `users` y uno de `user_levels`:

`TimezoneFromSessionMiddleware` → `AccountRegistryMiddleware` → `TwoFactorAuthMiddleware` →
`LoginRequiredMiddleware` → `InitialTrainingGateMiddleware` → `RouteLevelAccessMiddleware` →
`UpdateLastActivityMiddleware`, seguido de `django_htmx.middleware.HtmxMiddleware`.

---



## Desarrollo


| Herramienta            | Comando                                                                                                        |
| ---------------------- | -------------------------------------------------------------------------------------------------------------- |
| Lint / formato (Python)| `ruff check .` · `ruff format .` — configurado en `pyproject.toml`, longitud de línea 120                      |
| Lint / formato (JS)    | `biome check` — configurado en `biome.json`                                                                    |
| Tests                  | `.venv\Scripts\pytest.exe apps/<app>/tests/ -v` — pytest + pytest-django + factory-boy, `testpaths = ["apps"]` |
| Pre-commit             | `.pre-commit-config.yaml` es la autoridad de correcciones automáticas; no reviertas lo que aplica              |


Los mensajes de commit siguen **Conventional Commits** (`<type>(<scope>): <description>`, primera
línea ≤ 60 caracteres). Los releases y [`CHANGELOG.md`](CHANGELOG.md) los genera release-please.

### Espejo público de documentación

La documentación vive en este repositorio y se replica en
[`conectafam-plus-docs`](https://github.com/Anthony-JCG/conectafam-plus-docs) cuando un push a
`main` incluye cambios en `.md` versionados (excluyendo `.github/` y `.cursor/`). GitHub Actions
en ese repositorio construye el sitio MkDocs.

Workflow: [`.github/workflows/sync-docs.yml`](.github/workflows/sync-docs.yml).

---



## Índice de documentación


| Documento                                                    | Contenido                                                                                         |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| [`docs/docker.es.md`](docs/docker.es.md)                       | Arquitectura de contenedores, tres entornos, Nginx, entrypoint, volúmenes, CI/CD, migración systemd |
| [`docs/backups.es.md`](docs/backups.es.md)                     | Backup y restauración de base de datos                                                            |
| [`docs/user-levels-cache.es.md`](docs/user-levels-cache.es.md) | Caché Redis de `user_levels`: claves, TTL, invalidación, depuración                               |
| [`CHANGELOG.md`](CHANGELOG.md)                                 | Historial de releases                                                                             |
| `apps/*/README.es.md`                                          | Referencia por app — ver el [índice de aplicaciones](#índice-de-aplicaciones)                     |
