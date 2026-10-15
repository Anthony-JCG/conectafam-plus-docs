# MySQL backups to Cloudflare R2

Runbook for the nightly database dump. It applies to **production only** (MySQL on the host, Model B)
and runs on the server with `mysqldump`, `gzip` and `rclone` — it does not go through Django or
Celery. The surrounding deployment is documented in [docker.md](docker.md).

## Behaviour

| Aspect | Value |
|---|---|
| Schedule | Daily at **01:00 UTC** (`systemd` timer) |
| Destination | `r2-media:<bucket>/database-backups/<DB_NAME>_YYYYMMDDTHHMMSSZ.sql.gz` |
| Retention | The **7** most recent copies (by name/timestamp); pruning runs **only after** a successful upload |
| Tooling | `mysqldump --single-transaction`, `gzip`, `rclone` |

The R2 keys live only in rclone (`/root/.config/rclone/rclone.conf`, remote `[r2-media]`). The
backup environment file only names the destination: `RCLONE_REMOTE=r2-media:BUCKET_NAME`.

## Files in the repository

| Path | Purpose |
|---|---|
| [`scripts/backup_mysql_r2.sh`](../scripts/backup_mysql_r2.sh) | The job script |
| [`scripts/mysql-backup.env.example`](../scripts/mysql-backup.env.example) | Environment template (no R2 secrets) |
| [`scripts/mysql-backup.cnf.example`](../scripts/mysql-backup.cnf.example) | MySQL defaults template |
| [`scripts/systemd/platform-mysql-backup.service`](../scripts/systemd/platform-mysql-backup.service) | Oneshot unit |
| [`scripts/systemd/platform-mysql-backup.timer`](../scripts/systemd/platform-mysql-backup.timer) | Timer at 01:00 UTC |

## Server installation

Requirements: `mysqldump`, `gzip`, and `rclone` with the `[r2-media]` remote already configured (the
same one used for the media migration). The service runs as **root**, so it reads
`/root/.config/rclone/rclone.conf`.

### 1. MySQL credentials (outside git)

```bash
sudo mkdir -p /etc/platform
sudo cp /home/Platform/scripts/mysql-backup.cnf.example /etc/platform/mysql-backup.cnf
sudo cp /home/Platform/scripts/mysql-backup.env.example /etc/platform/mysql-backup.env
sudo chmod 600 /etc/platform/mysql-backup.cnf /etc/platform/mysql-backup.env
sudo chown root:root /etc/platform/mysql-backup.cnf /etc/platform/mysql-backup.env
```

Then edit:

- `/etc/platform/mysql-backup.cnf` — MySQL user and password.
- `/etc/platform/mysql-backup.env` — `RCLONE_REMOTE=r2-media:BUCKET_NAME` (the same bucket as media).

A dedicated MySQL user is recommended:

```sql
CREATE USER 'platform_backup'@'localhost' IDENTIFIED BY '...';
GRANT SELECT, SHOW VIEW, TRIGGER, EVENT, LOCK TABLES ON ConectaPlus.* TO 'platform_backup'@'localhost';
FLUSH PRIVILEGES;
```

In `/etc/platform/mysql-backup.cnf` use `host=localhost` (socket). Do **not** use `127.0.0.1`: that
is TCP, and MySQL then looks for `'platform_backup'@'127.0.0.1'`, a different account → error 1045.

The script uses `--no-tablespaces` (so the `PROCESS` privilege is not required) and calls rclone with
`--s3-no-check-bucket` (R2 usually denies `CreateBucket` to the token).

### 2. Script and units

After `git pull` in `/home/Platform`:

```bash
sudo cp /home/Platform/scripts/systemd/platform-mysql-backup.service /etc/systemd/system/
sudo cp /home/Platform/scripts/systemd/platform-mysql-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now platform-mysql-backup.timer
```

`chmod +x` is not needed on the server: the unit invokes `/bin/bash …/backup_mysql_r2.sh`. A local
`chmod` would dirty the working tree and break auto-deploy (`git checkout`/`reset`).

Manual test:

```bash
sudo systemctl start platform-mysql-backup.service
sudo journalctl -u platform-mysql-backup.service -e --no-pager
# or:
sudo bash /home/Platform/scripts/backup_mysql_r2.sh
rclone lsf r2-media:BUCKET_NAME/database-backups/
systemctl list-timers | grep platform-mysql
```

## Restoring a dump

```bash
rclone copyto r2-media:BUCKET_NAME/database-backups/ConectaPlus_YYYYMMDDTHHMMSSZ.sql.gz /tmp/restore.sql.gz
gunzip -c /tmp/restore.sql.gz | mysql --defaults-extra-file=/etc/platform/mysql-backup.cnf
```

The dump is taken with `--databases`, so it contains `CREATE DATABASE` / `USE`. Restore it on a test
host before touching production.

## Notes

- The timer uses `Persistent=true`: if the server was powered off at 01:00 UTC, the job runs on the
  next boot.
- There are no automatic backups of the test environment.
- Once MySQL moves into a container (Model A), the dump will have to be adapted to
  `docker compose exec db mysqldump` (or the container's host socket).
