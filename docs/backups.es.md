# Backups de MySQL a Cloudflare R2

Guía del volcado nocturno de la base de datos. Aplica **solo a producción**. MySQL corre en el
contenedor `db` del stack de Docker; el servidor lanza el job con `docker compose exec`, `gzip` y
`rclone`. No pasa por Django ni Celery. El despliegue está documentado en [docker.es.md](docker.es.md).

## Comportamiento

| Aspecto | Valor |
|---|---|
| Horario | Todos los días a las **01:00 UTC** (timer de `systemd`) |
| Destino | `r2-media:<bucket>/database-backups/<DB_NAME>_YYYYMMDDTHHMMSSZ.sql.gz` |
| Retención | Las **7** copias más recientes; la limpieza se hace **solo después** de subir bien la nueva |
| Herramientas | `docker compose exec db mysqldump --single-transaction`, `gzip`, `rclone` |

Las credenciales de MySQL se leen dentro del contenedor (`MYSQL_ROOT_PASSWORD`, que viene del
`.env`). Las claves de R2 están solo en rclone (`/root/.config/rclone/rclone.conf`, remote
`[r2-media]`). El archivo de entorno del backup solo indica la base de datos y el destino.

## Archivos del repositorio

| Ruta | Para qué sirve |
|---|---|
| [`scripts/backup_mysql_r2.sh`](../scripts/backup_mysql_r2.sh) | Script del job |
| [`scripts/mysql-backup.env.example`](../scripts/mysql-backup.env.example) | Plantilla de entorno (sin secretos) |
| [`scripts/systemd/impact-tech-mysql-backup.service`](../scripts/systemd/impact-tech-mysql-backup.service) | Unit oneshot |
| [`scripts/systemd/impact-tech-mysql-backup.timer`](../scripts/systemd/impact-tech-mysql-backup.timer) | Timer a las 01:00 UTC |

## Instalación en el servidor

En el servidor hace falta Docker con el stack corriendo en `/home/impact-tech`, `gzip` y `rclone`.
El servicio corre como **root**, así que lee `/root/.config/rclone/rclone.conf`.

### 1. Remote de rclone

```bash
sudo apt install -y rclone
sudo rclone config   # remote nuevo "r2-media", tipo s3, proveedor Cloudflare
```

Usa la access key, el secret y el endpoint de R2 (`https://<account_id>.r2.cloudflarestorage.com`).
Compruébalo con `sudo rclone lsd r2-media:`.

### 2. Entorno del backup (fuera de git)

```bash
sudo mkdir -p /etc/impact-tech
sudo cp /home/impact-tech/scripts/mysql-backup.env.example /etc/impact-tech/mysql-backup.env
sudo chmod 600 /etc/impact-tech/mysql-backup.env
sudo chown root:root /etc/impact-tech/mysql-backup.env
```

Edita `/etc/impact-tech/mysql-backup.env`: `DB_NAME` tiene que coincidir con el del `.env`, y
`RCLONE_REMOTE` apunta al bucket (`r2-media:impact-tech`).

### 3. Units

El deploy de producción copia y activa las units en cada release. Para instalarlas a mano:

```bash
sudo cp /home/impact-tech/scripts/systemd/impact-tech-mysql-backup.service /etc/systemd/system/
sudo cp /home/impact-tech/scripts/systemd/impact-tech-mysql-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now impact-tech-mysql-backup.timer
```

No hace falta `chmod +x` en el servidor: la unit invoca `/bin/bash …/backup_mysql_r2.sh`. Un `chmod`
local ensuciaría el árbol de trabajo y rompería el deploy (`git reset`).

Prueba manual:

```bash
sudo systemctl start impact-tech-mysql-backup.service
sudo journalctl -u impact-tech-mysql-backup.service -e --no-pager
sudo rclone lsf r2-media:impact-tech/database-backups/
systemctl list-timers | grep impact-tech-mysql
```

## Restaurar un volcado

```bash
cd /home/impact-tech
sudo rclone copyto r2-media:impact-tech/database-backups/<DB_NAME>_YYYYMMDDTHHMMSSZ.sql.gz /tmp/restore.sql.gz
gunzip -c /tmp/restore.sql.gz | docker compose exec -T db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"'
```

El volcado se hace con `--databases`, así que incluye `CREATE DATABASE` / `USE`. Pruébalo primero en
un servidor de pruebas antes de tocar producción.

## Notas

- El timer usa `Persistent=true`: si el servidor estaba apagado a las 01:00 UTC, el job se ejecuta
  al arrancar.
- El volumen `mysql_data` contiene los datos en vivo; nunca ejecutes `docker compose down -v` en
  producción.