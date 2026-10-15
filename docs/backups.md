# MySQL backups to Cloudflare R2

Runbook for the nightly database dump. It applies to **production only**. MySQL runs in the `db`
container of the Docker stack; the host runs the job with `docker compose exec`, `gzip` and
`rclone`. It does not go through Django or Celery. The deployment is documented in
[docker.md](docker.md).

## Behaviour

| Aspect | Value |
|---|---|
| Schedule | Daily at **01:00 UTC** (`systemd` timer) |
| Destination | `r2-media:<bucket>/database-backups/<DB_NAME>_YYYYMMDDTHHMMSSZ.sql.gz` |
| Retention | The **7** most recent copies; pruning runs **only after** a successful upload |
| Tooling | `docker compose exec db mysqldump --single-transaction`, `gzip`, `rclone` |

MySQL credentials are read inside the container (`MYSQL_ROOT_PASSWORD`, set from `.env`). The R2
keys live only in rclone (`/root/.config/rclone/rclone.conf`, remote `[r2-media]`). The backup
environment file only names the database and destination.

## Files in the repository

| Path | Purpose |
|---|---|
| [`scripts/backup_mysql_r2.sh`](../scripts/backup_mysql_r2.sh) | The job script |
| [`scripts/mysql-backup.env.example`](../scripts/mysql-backup.env.example) | Environment template (no secrets) |
| [`scripts/systemd/impact-tech-mysql-backup.service`](../scripts/systemd/impact-tech-mysql-backup.service) | Oneshot unit |
| [`scripts/systemd/impact-tech-mysql-backup.timer`](../scripts/systemd/impact-tech-mysql-backup.timer) | Timer at 01:00 UTC |

## Server installation

Requirements on the host: Docker with the stack running in `/home/impact-tech`, `gzip`, and
`rclone`. The service runs as **root**, so it reads `/root/.config/rclone/rclone.conf`.

### 1. rclone remote

```bash
sudo apt install -y rclone
sudo rclone config   # new remote "r2-media", type s3, provider Cloudflare
```

Use the R2 access key, secret and endpoint (`https://<account_id>.r2.cloudflarestorage.com`).
Check it with `sudo rclone lsd r2-media:`.

### 2. Backup environment (outside git)

```bash
sudo mkdir -p /etc/impact-tech
sudo cp /home/impact-tech/scripts/mysql-backup.env.example /etc/impact-tech/mysql-backup.env
sudo chmod 600 /etc/impact-tech/mysql-backup.env
sudo chown root:root /etc/impact-tech/mysql-backup.env
```

Edit `/etc/impact-tech/mysql-backup.env`: `DB_NAME` must match `.env`, and `RCLONE_REMOTE` points to
the bucket (`r2-media:impact-tech`).

### 3. Units

The production deploy copies and enables the units on every release. To install them by hand:

```bash
sudo cp /home/impact-tech/scripts/systemd/impact-tech-mysql-backup.service /etc/systemd/system/
sudo cp /home/impact-tech/scripts/systemd/impact-tech-mysql-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now impact-tech-mysql-backup.timer
```

`chmod +x` is not needed on the server: the unit invokes `/bin/bash …/backup_mysql_r2.sh`. A local
`chmod` would dirty the working tree and break the deploy (`git reset`).

Manual test:

```bash
sudo systemctl start impact-tech-mysql-backup.service
sudo journalctl -u impact-tech-mysql-backup.service -e --no-pager
sudo rclone lsf r2-media:impact-tech/database-backups/
systemctl list-timers | grep impact-tech-mysql
```

## Restoring a dump

```bash
cd /home/impact-tech
sudo rclone copyto r2-media:impact-tech/database-backups/<DB_NAME>_YYYYMMDDTHHMMSSZ.sql.gz /tmp/restore.sql.gz
gunzip -c /tmp/restore.sql.gz | docker compose exec -T db sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"'
```

The dump is taken with `--databases`, so it contains `CREATE DATABASE` / `USE`. Restore it on a test
host before touching production.

## Notes

- The timer uses `Persistent=true`: if the server was off at 01:00 UTC, the job runs on the next boot.
- The `mysql_data` volume is the live data; never run `docker compose down -v` in production.