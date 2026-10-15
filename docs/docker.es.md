# Despliegue en contenedores

Arquitectura Docker de Impact Tech: una aplicación web Django 5.2 en la que todos los servicios
(web, Celery, MySQL, Redis, Nginx) corren en contenedores. Este documento describe cómo se construye
el stack y cómo se opera en cada entorno.

## Resumen

| Componente | Implementación |
|---|---|
| Aplicación WSGI | Gunicorn (gevent, 1000 conexiones, timeout de 120 s) |
| Reverse proxy | Nginx (TLS, estáticos, medios HLS) |
| Tareas asíncronas | Celery worker + Celery beat |
| Caché / broker | Redis |
| Base de datos | MySQL 8 (`utf8mb4`) |
| Archivos estáticos | `collectstatic` en el build de la imagen; servidos por Nginx |
| Media | Volumen persistente `media_data` |

## Entornos

| Entorno | `.env` | Gunicorn | Celery |
|---|---|---|---|
| Desarrollo local | `DEBUG=1` | `runserver` | 1 contenedor, `CELERY_CONCURRENCY=1` |
| Test | `NGINX_CONFIG=test`, `TEST_ENVIRONMENT=1` | `GUNICORN_WORKERS=2` | `--scale celery-worker=2`, `CELERY_CONCURRENCY=1` |
| Producción | `NGINX_CONFIG=production` | `GUNICORN_WORKERS=10` | `--scale celery-worker=5`, `CELERY_CONCURRENCY=10` |

## Ajustes de Celery

| Parámetro | Configurado en |
|---|---|
| `CELERY_CONCURRENCY` | Variable de `.env`, la usa `docker-compose.yml` |
| Réplicas del servicio | `--scale celery-worker=N` en el comando de despliegue |

Docker Compose no interpola `--scale` desde `.env`; el número de réplicas se pasa en la línea de
comandos (test: 2, producción: 5).

## Servicios de datos

### Stack completo — Stack completo (por defecto)

`docker-compose.yml` arranca los contenedores `db` y `redis`. Máxima portabilidad y paridad entre
entornos: la misma definición funciona en cualquier host Docker.

## Arquitectura

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

## Configuración de Nginx

Se selecciona con `NGINX_CONFIG` en `.env`:

| Archivo | Dominio | Certificados |
|---|---|---|
| `docker/nginx/production.conf` | `impact-tech.app`, `www.impact-tech.app` | `/etc/letsencrypt/live/impact-tech.app/` |
| `docker/nginx/test.conf` | `debug.impact-tech.app` | `/etc/letsencrypt/live/debug.impact-tech.app/` |

Los certificados del host se montan en el contenedor: `/etc/letsencrypt:/etc/letsencrypt:ro`.

## Requisitos

- Docker Engine 24+
- Docker Compose v2
- Un archivo `.env` (plantilla: `.env.docker.example`)

## Operaciones

### Desarrollo local

```powershell
copy .env.docker.example .env
docker compose -f docker-compose.dev.yml up --build
```

Celery es opcional: añade `--profile workers`.

### Entorno de test

```bash
cd /home/impact-tech
docker compose up -d --build --scale celery-worker=2
```

Variables de `.env`: `NGINX_CONFIG=test`, `TEST_ENVIRONMENT=1`, `GUNICORN_WORKERS=2`,
`CELERY_CONCURRENCY=1`.

### Entorno de producción

```bash
cd /home/impact-tech
docker compose up -d --build --scale celery-worker=5
```

Variables de `.env`: `NGINX_CONFIG=production`, `GUNICORN_WORKERS=10`, `CELERY_CONCURRENCY=10`.

### Actualización de versión

```bash
cd /home/impact-tech
git pull
docker compose up -d --build --scale celery-worker=5
```

Para cambios solo en `.env` (sin rebuild):

```bash
docker compose up -d --scale celery-worker=5
```

Sustituye `5` por `2` en el entorno de test.

### Validación

```bash
docker compose ps
docker compose logs -f web
curl -I https://impact-tech.app
curl -I https://debug.impact-tech.app
```

## Volúmenes

| Clave Compose | Contenido |
|---|---|
| `media_data` | Archivos subidos y segmentos HLS |
| `mysql_data` | Datos de MySQL |
| `redis_data` | Persistencia AOF de Redis |
| *(ninguno para beat)* | El schedule de Celery beat vive en `/app/celerybeat-data` dentro del contenedor — sin volumen, lo que evita volúmenes Docker propiedad de root |


Los estáticos son **artefactos de build**: `collectstatic` se ejecuta en el `Dockerfile` de la app
(escribiendo en `/app/staticfiles`) y la imagen **nginx** copia ese mismo árbol desde la imagen
`impact-tech-app` (`docker/Dockerfile.nginx` → `/var/www/static/`). Django y nginx comparten exactamente
el mismo manifiesto; no hay volumen ni directorio en el host.

En cada deploy: `docker compose build web`, luego `docker compose build nginx`, y después `up`. Si
`/static/` devuelve 404: `docker compose exec nginx ls /var/www/static/js/home-modals*.js`.

## Entrypoint (`docker/entrypoint.sh`)

Todos los contenedores comparten la misma imagen; el entrypoint decide qué hacer según el comando de
arranque (`$1`).

### Migraciones de base de datos

| Comando de arranque (`$1`) | Servicio | Ejecuta `migrate` |
|---|---|---|
| `gunicorn` | `web` (producción/test) | Sí |
| `python` | `web` en desarrollo (`runserver`) | Sí |
| `pytest` | CI (`docker-compose.ci.yml`) | Sí |
| `celery` | `celery-worker`, `celery-beat` | No |

Solo el proceso que arranca la aplicación web (o los tests de CI) aplica migraciones. Celery no lo
hace, lo que evita condiciones de carrera contra MySQL cuando varios contenedores se despliegan a la
vez.

### Otras acciones del entrypoint

| Condición | Acción |
|---|---|
| `DEBUG != 1` | Espera TCP en MySQL y Redis |
| Build de la imagen | `collectstatic` + `docker/verify_collectstatic.py`; escribe `.static_version` |

### Orden de arranque (producción)

1. `db` y `redis` pasan sus healthchecks.
2. `web` espera los datos, ejecuta `migrate` y arranca Gunicorn.
3. `celery-worker` y `celery-beat` esperan `web: service_healthy` (Gunicorn respondiendo en `:8080`).
4. `nginx` hace proxy hacia `web`.

## Comandos de administración

```bash
docker compose exec web python manage.py createsuperuser
docker compose logs -f web celery-worker
docker compose down
docker compose down -v    # removes volumes, including media
```

## Integración continua (GitHub Actions)

El workflow `.github/workflows/django-tests.yml` ejecuta pytest dentro del contenedor `web` usando
`docker-compose.ci.yml`: Redis en contenedor, `DEBUG=1` (SQLite), sin nginx, Celery ni MySQL.
Valida el `Dockerfile` en cada PR que toque código Python.

| Entorno | MySQL / Redis |
|---|---|
| CI | Redis en contenedor; SQLite para los tests |
| Servidores | Contenedores `db` y `redis` |

## Copias de seguridad de la base de datos

En producción (MySQL en el host), los dumps diarios a Cloudflare R2 están documentados en
[backups.es.md](backups.es.md) (`scripts/backup_mysql_r2.sh` + timer de systemd a las 01:00 UTC).

## Despliegue continuo

Workflow: [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml).

| Disparador | Destino |
|---|---|
| Push a `main` | Servidor de test |
| Tag `v*` (Release Please) | Servidor de producción |

Antes del paso SSH, un job detecta cambios con `dorny/paths-filter` (diff respecto al commit
anterior en `main`, o respecto al tag anterior en releases). Rebuild selectivo:

| Cambio | `docker compose build web` | `docker compose build nginx` |
|---|---|---|
| App Python / requirements / `Dockerfile` / estáticos / templates / entrypoint / gunicorn | Sí | Sí (nginx copia staticfiles desde la imagen de la app) |
| Solo `docker/nginx/**` o `Dockerfile.nginx` | No | Sí |
| Solo docs / scripts / workflows | No | No (aún así se ejecuta `up -d`) |

La app de producción **no monta código del host**: vive en la imagen. Por eso cualquier cambio en
código, requirements, estáticos o migraciones exige un rebuild — un `git reset` a secas no
actualiza los contenedores. `.env` no está en git y se aplica en runtime con `up -d`, sin
rebuild.

En el host, ejecuta siempre `git fetch` + `git reset --hard` (limpia suciedad en archivos
rastreados, por ejemplo un `chmod` local) y después `up -d`. Deliberadamente no se usa `git clean`,
para preservar el `.env`, que no está en git.

## Referencia de archivos

| Archivo | Propósito |
|---|---|
| `Dockerfile` | Imagen de la app e imagen de nginx |
| `docker-compose.yml` | Stack base |
| `docker-compose.dev.yml` | Stack de desarrollo local (aislado, SQLite) |
| `docker-compose.ci.yml` | Override de CI (pytest en contenedor) |
| `.env.docker.example` | Plantilla de variables |
| `scripts/backup_mysql_r2.sh` | Backup MySQL → R2 (ver [backups.es.md](backups.es.md)) |
