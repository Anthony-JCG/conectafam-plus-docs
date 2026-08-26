# Despliegue en contenedores

Arquitectura Docker de Conectafam Plus: una aplicación web Django 5.2 alineada con la
configuración de referencia en `production_settings/`. Este documento describe cómo se construye el
stack, cómo se opera en cada entorno y cómo migrar un despliegue systemd existente hacia él.

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

| Parámetro | Configurado en | Equivalente systemd |
|---|---|---|
| `CELERY_CONCURRENCY` | Variable de `.env`, consumida por `docker-compose.yml` | `--concurrency` en cada unit |
| Réplicas del servicio | Flag `--scale celery-worker=N` en el comando de deploy | N units `celery-worker@{1..N}` |

Docker Compose no interpola `--scale` desde `.env`; el número de réplicas se pasa en la línea de
comandos (test: 2, producción: 5).

## Modelos de despliegue de datos

### Modelo A — Stack completo (por defecto)

`docker-compose.yml` arranca los contenedores `db` y `redis`. Máxima portabilidad y paridad entre
entornos: la misma definición funciona en cualquier host Docker.

### Modelo B — MySQL/Redis en el host (migración)

`docker-compose.host-services.yml` desactiva los contenedores `db`/`redis`. **web**, **celery** y
**nginx** usan `network_mode: host`: la app habla con MySQL/Redis en `127.0.0.1` y nginx hace proxy
hacia `127.0.0.1:8080` (`docker/nginx/${NGINX_CONFIG}.host.conf`).

En Linux, un contenedor en red bridge **no puede** alcanzar MySQL en el `127.0.0.1` del host
(`Waiting for host.docker.internal:3306`) ni, con UFW activo, Gunicorn a través de
`host.docker.internal:8080` (curl a `127.0.0.1:8080` en el host funciona, pero el HTTPS vía nginx
se queda colgado).

Limitaciones:

- Acoplado a un host concreto (rutas, sockets, firewall).
- Solo un proceso puede escuchar en los puertos 80/443 del host (detener el nginx de systemd antes del stack).
- No se puede reproducir en otra máquina sin servicios de host equivalentes.

**Recomendación:** el Modelo A es la arquitectura objetivo. Usa el Modelo B solo durante la
transición y planifica la migración de datos a un contenedor o a un servicio gestionado.

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
         (Model A)            (Model A)          celery-beat
```

## Configuración de Nginx

Se selecciona con `NGINX_CONFIG` en `.env`:

| Archivo | Dominio | Certificados |
|---|---|---|
| `docker/nginx/production.conf` | `conectafam-plus.com`, `www.conectafam-plus.com` | `/etc/letsencrypt/live/conectafam-plus.com/` |
| `docker/nginx/test.conf` | `debug.conectafam-plus.com` | `/etc/letsencrypt/live/debug.conectafam-plus.com/` |

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
cd /home/Platform
docker compose up -d --build --scale celery-worker=2
```

Variables de `.env`: `NGINX_CONFIG=test`, `TEST_ENVIRONMENT=1`, `GUNICORN_WORKERS=2`,
`CELERY_CONCURRENCY=1`.

### Entorno de producción

```bash
cd /home/Platform
docker compose up -d --build --scale celery-worker=5
```

Variables de `.env`: `NGINX_CONFIG=production`, `GUNICORN_WORKERS=10`, `CELERY_CONCURRENCY=10`.

### Actualización de versión

```bash
cd /home/Platform
git pull
docker compose up -d --build --scale celery-worker=5
```

Para cambios solo en `.env` (sin rebuild):

```bash
docker compose up -d --scale celery-worker=5
```

Sustituye `5` por `2` en el entorno de test.

## Migración desde un despliegue systemd

### Prerrequisitos

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
```

### Código y variables

```bash
cd /home/Platform
git pull
```

Conserva el `.env` existente del servidor. Añade las variables que falten: `NGINX_CONFIG`,
`GUNICORN_WORKERS`, `CELERY_CONCURRENCY`, `NGINX_HTTP_PORT`, `NGINX_HTTPS_PORT`.

### MySQL/Redis en el host (Modelo B, opcional)

```bash
cp docker-compose.host-services.yml docker-compose.override.yml
```

### Desactivar las units de systemd

**Obligatorio antes de `docker compose up` bajo el Modelo B** (`docker-compose.override.yml` →
`network_mode: host`). Si la unit `gunicorn` de systemd sigue activa, el contenedor `web` no puede
enlazar el puerto 8080 (`Address already in use`) mientras nginx sigue sirviendo tráfico desde el
proceso antiguo del host.

Detén y deshabilita las units que sustituyen los contenedores (puertos 80, 443 y **8080**):

```bash
sudo systemctl stop gunicorn celery-beat nginx
sudo systemctl stop 'celery-worker@*'
sudo systemctl disable gunicorn celery-beat nginx
sudo systemctl disable celery-worker@{1..5}
ss -tlnp | grep ':8080'   # no host gunicorn should remain
docker compose up -d --build --scale celery-worker=5
```

Si el sitio responde pero `docker compose logs web` muestra `Address already in use`, el tráfico lo
sigue sirviendo **gunicorn de systemd**, no el contenedor.

Las units `mysql` y `redis-server` del host solo permanecen activas bajo el Modelo B.

### Migración de media

El volumen lógico `media_data` se monta en `/app/media` del servicio `web`. No hace falta conocer el
nombre interno del volumen Docker (`platform_media_data`); basta con el servicio de Compose:

```bash
docker compose build web
docker compose run --rm --user root --entrypoint sh \
  -v /home/Platform/media:/src:ro \
  web -c "cp -a /src/. /app/media/ && chown -R app:app /app/media"
```

El volumen `media_data` se crea como root mientras el proceso `web` corre como el usuario `app`, así
que la copia debe ejecutarse como root y corregir la propiedad después.

Convención de nombres de Docker Compose: `name` del proyecto (`platform`) + clave del volumen
(`media_data`) → volumen físico `platform_media_data`. Solo es relevante al inspeccionar con
`docker volume inspect`.

### Validación

```bash
docker compose ps
docker compose logs -f web
curl -I https://conectafam-plus.com
curl -I https://debug.conectafam-plus.com
```

## Volúmenes

| Clave Compose | Contenido |
|---|---|
| `media_data` | Archivos subidos y segmentos HLS |
| `mysql_data` | Datos de MySQL (Modelo A) |
| `redis_data` | Persistencia AOF de Redis (Modelo A) |
| *(ninguno para beat)* | El schedule de Celery beat vive en `/app/celerybeat-data` dentro del contenedor — sin volumen, lo que evita volúmenes Docker propiedad de root |

Tras migrar desde un despliegue que usaba un volumen `celerybeat_data`, el volumen huérfano se puede
eliminar: `docker volume rm platform_celerybeat_data`.

Los estáticos son **artefactos de build**: `collectstatic` se ejecuta en el `Dockerfile` de la app
(escribiendo en `/app/staticfiles`) y la imagen **nginx** copia ese mismo árbol desde la imagen
`platform-app` (`docker/Dockerfile.nginx` → `/var/www/static/`). Django y nginx comparten exactamente
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
| `$1 = gunicorn` | Comprueba que el puerto de bind esté libre |
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
| Servidores (transición) | Modelo B: servicios del host vía `docker-compose.host-services.yml` |
| Servidores (objetivo) | Modelo A: contenedores `db` y `redis` |

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
para preservar el `.env` y el `docker-compose.override.yml` no rastreados.

## Referencia de archivos

| Archivo | Propósito |
|---|---|
| `Dockerfile` | Imagen de la app e imagen de nginx |
| `docker-compose.yml` | Stack base (Modelo A) |
| `docker-compose.dev.yml` | Stack de desarrollo local (aislado, SQLite) |
| `docker-compose.host-services.yml` | Plantilla del Modelo B (migración) |
| `docker-compose.ci.yml` | Override de CI (pytest en contenedor) |
| `.env.docker.example` | Plantilla de variables |
| `scripts/backup_mysql_r2.sh` | Backup MySQL → R2 (ver [backups.es.md](backups.es.md)) |
