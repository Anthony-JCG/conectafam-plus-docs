# Backups de MySQL a Cloudflare R2

Runbook del dump nocturno de la base de datos. Aplica solo a **producción** (MySQL en el host,
Modelo B) y corre en el servidor con `mysqldump`, `gzip` y `rclone`: no pasa por Django ni Celery.
El despliegue asociado está documentado en [docker.es.md](docker.es.md).

## Comportamiento

| Aspecto | Valor |
|---|---|
| Horario | Diario a las **01:00 UTC** (timer de `systemd`) |
| Destino | `r2-media:<bucket>/database-backups/<DB_NAME>_YYYYMMDDTHHMMSSZ.sql.gz` |
| Retención | Las **7** copias más recientes (por nombre/timestamp); el prune corre **solo después** de un upload correcto |
| Herramientas | `mysqldump --single-transaction`, `gzip`, `rclone` |

Las keys de R2 viven solo en rclone (`/root/.config/rclone/rclone.conf`, remote `[r2-media]`). El
archivo de entorno del backup solo indica el destino: `RCLONE_REMOTE=r2-media:BUCKET_NAME`.

## Archivos en el repositorio

| Ruta | Uso |
|---|---|
| [`scripts/backup_mysql_r2.sh`](../scripts/backup_mysql_r2.sh) | Script del job |
| [`scripts/mysql-backup.env.example`](../scripts/mysql-backup.env.example) | Plantilla de entorno (sin secretos R2) |
| [`scripts/mysql-backup.cnf.example`](../scripts/mysql-backup.cnf.example) | Plantilla de defaults MySQL |
| [`scripts/systemd/platform-mysql-backup.service`](../scripts/systemd/platform-mysql-backup.service) | Unit oneshot |
| [`scripts/systemd/platform-mysql-backup.timer`](../scripts/systemd/platform-mysql-backup.timer) | Timer a las 01:00 UTC |

## Instalación en el servidor

Requisitos: `mysqldump`, `gzip` y `rclone` con el remote `[r2-media]` ya configurado (el mismo de la
migración de media). El servicio corre como **root**, así que lee
`/root/.config/rclone/rclone.conf`.

### 1. Credenciales MySQL (fuera de git)

```bash
sudo mkdir -p /etc/platform
sudo cp /home/Platform/scripts/mysql-backup.cnf.example /etc/platform/mysql-backup.cnf
sudo cp /home/Platform/scripts/mysql-backup.env.example /etc/platform/mysql-backup.env
sudo chmod 600 /etc/platform/mysql-backup.cnf /etc/platform/mysql-backup.env
sudo chown root:root /etc/platform/mysql-backup.cnf /etc/platform/mysql-backup.env
```

Luego edita:

- `/etc/platform/mysql-backup.cnf` — usuario y contraseña MySQL.
- `/etc/platform/mysql-backup.env` — `RCLONE_REMOTE=r2-media:BUCKET_NAME` (el mismo bucket que media).

Se recomienda un usuario MySQL dedicado:

```sql
CREATE USER 'platform_backup'@'localhost' IDENTIFIED BY '...';
GRANT SELECT, SHOW VIEW, TRIGGER, EVENT, LOCK TABLES ON ConectaPlus.* TO 'platform_backup'@'localhost';
FLUSH PRIVILEGES;
```

En `/etc/platform/mysql-backup.cnf` usa `host=localhost` (socket). **No** uses `127.0.0.1`: eso es
TCP y MySQL busca `'platform_backup'@'127.0.0.1'`, otra cuenta → error 1045.

El script usa `--no-tablespaces` (no hace falta el privilegio `PROCESS`) y llama a rclone con
`--s3-no-check-bucket` (R2 suele denegar `CreateBucket` al token).

### 2. Script y units

Tras `git pull` en `/home/Platform`:

```bash
sudo cp /home/Platform/scripts/systemd/platform-mysql-backup.service /etc/systemd/system/
sudo cp /home/Platform/scripts/systemd/platform-mysql-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now platform-mysql-backup.timer
```

No hace falta `chmod +x` en el servidor: la unit invoca `/bin/bash …/backup_mysql_r2.sh`. Un
`chmod` local ensuciaría el working tree y rompería el auto-deploy (`git checkout`/`reset`).

Prueba manual:

```bash
sudo systemctl start platform-mysql-backup.service
sudo journalctl -u platform-mysql-backup.service -e --no-pager
# o:
sudo bash /home/Platform/scripts/backup_mysql_r2.sh
rclone lsf r2-media:BUCKET_NAME/database-backups/
systemctl list-timers | grep platform-mysql
```

## Restaurar un dump

```bash
rclone copyto r2-media:BUCKET_NAME/database-backups/ConectaPlus_YYYYMMDDTHHMMSSZ.sql.gz /tmp/restore.sql.gz
gunzip -c /tmp/restore.sql.gz | mysql --defaults-extra-file=/etc/platform/mysql-backup.cnf
```

El dump se toma con `--databases`, así que incluye `CREATE DATABASE` / `USE`. Restáuralo en un host
de prueba antes de tocar producción.

## Notas

- El timer usa `Persistent=true`: si el servidor estaba apagado a las 01:00 UTC, el job se ejecuta
  en el siguiente arranque.
- No hay backups automáticos del entorno de test.
- Cuando MySQL pase a contenedor (Modelo A), habrá que adaptar el dump a
  `docker compose exec db mysqldump` (o al socket del host del contenedor).
