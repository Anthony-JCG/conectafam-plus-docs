# Containerised deployment

Docker architecture of Impact Tech: a Django 5.2 web application stack where every service (web,
Celery, MySQL, Redis, Nginx) runs in a container. This document covers how the stack is built and how
it is operated in each environment.

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

| Parameter | Configured in |
|---|---|
| `CELERY_CONCURRENCY` | `.env` variable, consumed by `docker-compose.yml` |
| Service replicas | `--scale celery-worker=N` flag on the deploy command |

Docker Compose does not interpolate `--scale` from `.env`; the replica count is passed on the command
line (test: 2, production: 5).

## Data services

### Full stack — Full stack (default)

`docker-compose.yml` starts `db` and `redis` containers. Maximum portability and parity between
environments: the same definition works on any Docker host.

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
                                                 celery-beat
```

## Nginx configuration

Selected through `NGINX_CONFIG` in `.env`:

| File | Domain | Certificates |
|---|---|---|
| `docker/nginx/production.conf` | `impact-tech.app`, `www.impact-tech.app` | `/etc/letsencrypt/live/impact-tech.app/` |
| `docker/nginx/test.conf` | `debug.impact-tech.app` | `/etc/letsencrypt/live/debug.impact-tech.app/` |

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
cd /home/impact-tech
docker compose up -d --build --scale celery-worker=2
```

`.env` variables: `NGINX_CONFIG=test`, `TEST_ENVIRONMENT=1`, `GUNICORN_WORKERS=2`,
`CELERY_CONCURRENCY=1`.

### Production environment

```bash
cd /home/impact-tech
docker compose up -d --build --scale celery-worker=5
```

`.env` variables: `NGINX_CONFIG=production`, `GUNICORN_WORKERS=10`, `CELERY_CONCURRENCY=10`.

### Version update

```bash
cd /home/impact-tech
git pull
docker compose up -d --build --scale celery-worker=5
```

For `.env`-only changes (no rebuild):

```bash
docker compose up -d --scale celery-worker=5
```

Replace `5` with `2` in the test environment.

### Validation

```bash
docker compose ps
docker compose logs -f web
curl -I https://impact-tech.app
curl -I https://debug.impact-tech.app
```

## Volumes

| Compose key | Contents |
|---|---|
| `media_data` | Uploaded files and HLS segments |
| `mysql_data` | MySQL data |
| `redis_data` | Redis AOF persistence |
| *(none for beat)* | The Celery beat schedule lives at `/app/celerybeat-data` inside the container — no volume, which avoids root-owned Docker volumes |


Static files are **build artefacts**: `collectstatic` runs in the app `Dockerfile` (writing to
`/app/staticfiles`) and the **nginx** image copies that same tree from the `impact-tech-app` image
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
| Servers | `db` and `redis` containers |

## Database backups

In production, daily dumps to Cloudflare R2 are documented in
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
example a local `chmod`) and then `up -d`. `git clean` is deliberately not used, so the untracked `.env` is
preserved.

## File reference

| File | Purpose |
|---|---|
| `Dockerfile` | App image and nginx image |
| `docker-compose.yml` | Base stack (`db` and `redis` included) |
| `docker-compose.dev.yml` | Local development stack (isolated, SQLite) |
| `docker-compose.ci.yml` | CI override (pytest in a container) |
| `.env.docker.example` | Variable template |
| `scripts/backup_mysql_r2.sh` | MySQL → R2 backup (see [backups.md](backups.md)) |
