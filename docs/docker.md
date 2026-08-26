# Containerised deployment

Docker architecture of Conectafam Plus: a Django 5.2 web application stack, aligned with the
reference configuration in `production_settings/`. This document covers how the stack is built, how
it is operated in each environment, and how to migrate an existing systemd deployment onto it.

## Overview

| Component | Implementation |
|---|---|
| WSGI application | Gunicorn (gevent, 1000 connections, 120 s timeout) |
| Reverse proxy | Nginx (TLS, static files, HLS media) |
| Asynchronous tasks | Celery worker + Celery beat |
| Cache / broker | Redis |
| Database | MySQL 8 (`utf8mb4`) |
| Static files | `collectstatic` at image build time; served by Nginx |
| Media | Persistent `media_data` volume |

## Environments

| Environment | `.env` | Gunicorn | Celery |
|---|---|---|---|
| Local development | `DEBUG=1` | `runserver` | 1 container, `CELERY_CONCURRENCY=1` |
| Test | `NGINX_CONFIG=test`, `TEST_ENVIRONMENT=1` | `GUNICORN_WORKERS=2` | `--scale celery-worker=2`, `CELERY_CONCURRENCY=1` |
| Production | `NGINX_CONFIG=production` | `GUNICORN_WORKERS=10` | `--scale celery-worker=5`, `CELERY_CONCURRENCY=10` |

## Celery settings

| Parameter | Configured in | systemd equivalent |
|---|---|---|
| `CELERY_CONCURRENCY` | `.env` variable, consumed by `docker-compose.yml` | `--concurrency` on each unit |
| Service replicas | `--scale celery-worker=N` flag on the deploy command | N `celery-worker@{1..N}` units |

Docker Compose does not interpolate `--scale` from `.env`; the replica count is passed on the command
line (test: 2, production: 5).

## Data deployment models

### Model A — Full stack (default)

`docker-compose.yml` starts `db` and `redis` containers. Maximum portability and parity between
environments: the same definition works on any Docker host.

### Model B — MySQL/Redis on the host (migration)

`docker-compose.host-services.yml` disables the `db`/`redis` containers. **web**, **celery** and
**nginx** use `network_mode: host`: the app talks to MySQL/Redis on `127.0.0.1` and nginx proxies to
`127.0.0.1:8080` (`docker/nginx/${NGINX_CONFIG}.host.conf`).

On Linux, a bridge-network container **cannot** reach MySQL on the host's `127.0.0.1`
(`Waiting for host.docker.internal:3306`) nor, with UFW enabled, Gunicorn through
`host.docker.internal:8080` (curl to `127.0.0.1:8080` on the host works, but HTTPS through nginx
hangs).

Limitations:

- Coupled to one specific host (paths, sockets, firewall).
- Only one process can listen on host ports 80/443 (stop the systemd nginx before the stack).
- Cannot be reproduced on another machine without equivalent host services.

**Recommendation:** Model A is the target architecture. Use Model B only during the transition, and
plan the data migration to a container or a managed service.

## Architecture

```
                    ┌─────────────────────────────────────┐
  Client (HTTPS)    │  nginx container                    │
        ──────────► │  :443  TLS (Let's Encrypt)          │
                    │  /static/  → image (collectstatic)  │
                    │  /media/   → media_data volume      │
                    └──────────────┬──────────────────────┘
                                   │ TCP web:8080
                    ┌──────────────▼──────────────────────┐
                    │  web container (Gunicorn/gevent)    │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
        db container        redis container      celery-worker × N (--scale)
         (Model A)            (Model A)          celery-beat
```

## Nginx configuration

Selected through `NGINX_CONFIG` in `.env`:

| File | Domain | Certificates |
|---|---|---|
| `docker/nginx/production.conf` | `conectafam-plus.com`, `www.conectafam-plus.com` | `/etc/letsencrypt/live/conectafam-plus.com/` |
| `docker/nginx/test.conf` | `debug.conectafam-plus.com` | `/etc/letsencrypt/live/debug.conectafam-plus.com/` |

Host certificates are mounted into the container: `/etc/letsencrypt:/etc/letsencrypt:ro`.

## Requirements

- Docker Engine 24+
- Docker Compose v2
- An `.env` file (template: `.env.docker.example`)

## Operations

### Local development

```powershell
copy .env.docker.example .env
docker compose -f docker-compose.dev.yml up --build
```

Celery is optional: add `--profile workers`.

### Test environment

```bash
cd /home/Platform
docker compose up -d --build --scale celery-worker=2
```

`.env` variables: `NGINX_CONFIG=test`, `TEST_ENVIRONMENT=1`, `GUNICORN_WORKERS=2`,
`CELERY_CONCURRENCY=1`.

### Production environment

```bash
cd /home/Platform
docker compose up -d --build --scale celery-worker=5
```

`.env` variables: `NGINX_CONFIG=production`, `GUNICORN_WORKERS=10`, `CELERY_CONCURRENCY=10`.

### Version update

```bash
cd /home/Platform
git pull
docker compose up -d --build --scale celery-worker=5
```

For `.env`-only changes (no rebuild):

```bash
docker compose up -d --scale celery-worker=5
```

Replace `5` with `2` in the test environment.

## Migration from a systemd deployment

### Prerequisites

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
```

### Code and variables

```bash
cd /home/Platform
git pull
```

Keep the server's existing `.env`. Add any missing variables: `NGINX_CONFIG`, `GUNICORN_WORKERS`,
`CELERY_CONCURRENCY`, `NGINX_HTTP_PORT`, `NGINX_HTTPS_PORT`.

### MySQL/Redis on the host (Model B, optional)

```bash
cp docker-compose.host-services.yml docker-compose.override.yml
```

### Disabling the systemd units

**Mandatory before `docker compose up` under Model B** (`docker-compose.override.yml` →
`network_mode: host`). If the systemd `gunicorn` unit is still running, the `web` container cannot
bind port 8080 (`Address already in use`) while nginx keeps serving traffic from the old host
process.

Stop and disable the units replaced by containers (ports 80, 443 and **8080**):

```bash
sudo systemctl stop gunicorn celery-beat nginx
sudo systemctl stop 'celery-worker@*'
sudo systemctl disable gunicorn celery-beat nginx
sudo systemctl disable celery-worker@{1..5}
ss -tlnp | grep ':8080'   # no host gunicorn should remain
docker compose up -d --build --scale celery-worker=5
```

If the site responds but `docker compose logs web` shows `Address already in use`, traffic is still
being served by **systemd gunicorn**, not by the container.

The host `mysql` and `redis-server` units stay active only under Model B.

### Media migration

The logical `media_data` volume is mounted at `/app/media` in the `web` service. There is no need to
know the internal Docker volume name (`platform_media_data`); the Compose service is enough:

```bash
docker compose build web
docker compose run --rm --user root --entrypoint sh \
  -v /home/Platform/media:/src:ro \
  web -c "cp -a /src/. /app/media/ && chown -R app:app /app/media"
```

The `media_data` volume is created as root while the `web` process runs as the `app` user, so the
copy must run as root and fix ownership afterwards.

Docker Compose naming convention: project `name` (`platform`) + volume key (`media_data`) → physical
volume `platform_media_data`. Only relevant when inspecting with `docker volume inspect`.

### Validation

```bash
docker compose ps
docker compose logs -f web
curl -I https://conectafam-plus.com
curl -I https://debug.conectafam-plus.com
```

## Volumes

| Compose key | Contents |
|---|---|
| `media_data` | Uploaded files and HLS segments |
| `mysql_data` | MySQL data (Model A) |
| `redis_data` | Redis AOF persistence (Model A) |
| *(none for beat)* | The Celery beat schedule lives at `/app/celerybeat-data` inside the container — no volume, which avoids root-owned Docker volumes |

After migrating from a deployment that used a `celerybeat_data` volume, the orphaned volume can be
removed: `docker volume rm platform_celerybeat_data`.

Static files are **build artefacts**: `collectstatic` runs in the app `Dockerfile` (writing to
`/app/staticfiles`) and the **nginx** image copies that same tree from the `platform-app` image
(`docker/Dockerfile.nginx` → `/var/www/static/`). Django and nginx therefore share exactly the same
manifest; there is no volume and no host directory.

On every deploy: `docker compose build web`, then `docker compose build nginx`, then `up`. If
`/static/` returns 404: `docker compose exec nginx ls /var/www/static/js/home-modals*.js`.

## Entrypoint (`docker/entrypoint.sh`)

Every container shares the same image; the entrypoint decides what to do based on the start command
(`$1`).

### Database migrations

| Start command (`$1`) | Service | Runs `migrate` |
|---|---|---|
| `gunicorn` | `web` (production/test) | Yes |
| `python` | `web` in development (`runserver`) | Yes |
| `pytest` | CI (`docker-compose.ci.yml`) | Yes |
| `celery` | `celery-worker`, `celery-beat` | No |

Only the process that starts the web application (or the CI tests) applies migrations. Celery does
not, which avoids races against MySQL when several containers deploy at once.

### Other entrypoint actions

| Condition | Action |
|---|---|
| `DEBUG != 1` | Waits for TCP on MySQL and Redis |
| `$1 = gunicorn` | Checks that the bind port is free |
| Image build | `collectstatic` + `docker/verify_collectstatic.py`; writes `.static_version` |

### Startup order (production)

1. `db` and `redis` pass their healthchecks.
2. `web` waits for data, runs `migrate` and starts Gunicorn.
3. `celery-worker` and `celery-beat` wait for `web: service_healthy` (Gunicorn answering on `:8080`).
4. `nginx` proxies to `web`.

## Administration commands

```bash
docker compose exec web python manage.py createsuperuser
docker compose logs -f web celery-worker
docker compose down
docker compose down -v    # removes volumes, including media
```

## Continuous integration (GitHub Actions)

The `.github/workflows/django-tests.yml` workflow runs pytest inside the `web` container using
`docker-compose.ci.yml`: Redis in a container, `DEBUG=1` (SQLite), no nginx, Celery or MySQL. It
validates the `Dockerfile` on every PR that touches Python code.

| Environment | MySQL / Redis |
|---|---|
| CI | Redis in a container; SQLite for tests |
| Servers (transitional) | Model B: host services through `docker-compose.host-services.yml` |
| Servers (target) | Model A: `db` and `redis` containers |

## Database backups

In production (MySQL on the host), daily dumps to Cloudflare R2 are documented in
[backups.md](backups.md) (`scripts/backup_mysql_r2.sh` + systemd timer at 01:00 UTC).

## Continuous deployment

Workflow: [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml).

| Trigger | Target |
|---|---|
| Push to `main` | Test server |
| Tag `v*` (Release Please) | Production server |

Before the SSH step, a job detects changes with `dorny/paths-filter` (diff against the previous
commit on `main`, or against the previous tag on releases). Selective rebuild:

| Change | `docker compose build web` | `docker compose build nginx` |
|---|---|---|
| Python app / requirements / `Dockerfile` / static / templates / entrypoint / gunicorn | Yes | Yes (nginx copies staticfiles from the app image) |
| Only `docker/nginx/**` or `Dockerfile.nginx` | No | Yes |
| Only docs / scripts / workflows | No | No (`up -d` still runs) |

The production app **does not mount host code**: it lives in the image. That is why any change to
code, requirements, static files or migrations requires a rebuild — a bare `git reset` does not
update the containers. `.env` is not in git and is applied at runtime with `up -d`, without a
rebuild.

On the host, always run `git fetch` + `git reset --hard` (which clears dirt on tracked files, for
example a local `chmod`) and then `up -d`. `git clean` is deliberately not used, so untracked `.env`
and `docker-compose.override.yml` are preserved.

## File reference

| File | Purpose |
|---|---|
| `Dockerfile` | App image and nginx image |
| `docker-compose.yml` | Base stack (Model A) |
| `docker-compose.dev.yml` | Local development stack (isolated, SQLite) |
| `docker-compose.host-services.yml` | Model B template (migration) |
| `docker-compose.ci.yml` | CI override (pytest in a container) |
| `.env.docker.example` | Variable template |
| `scripts/backup_mysql_r2.sh` | MySQL → R2 backup (see [backups.md](backups.md)) |
