# Documentation

Infrastructure and operations documentation for Conectafam Plus. These are **topic guides and
runbooks**: how the system is deployed, operated and debugged.

Application-level reference — models, services, endpoints, access rules — is not here. It lives next
to the code, in each app's `README.md`. The [root README](../README.md) indexes all of them.

| Document | Contents |
|---|---|
| [docker.md](docker.md) | Container architecture, the three environments, Nginx, entrypoint, volumes, CI/CD and migration from systemd |
| [backups.md](backups.md) | Nightly MySQL dump to Cloudflare R2: installation, retention and restore procedure |
| [user-levels-cache.md](user-levels-cache.md) | Redis cache behind `user_levels`: keys, TTL, invalidation signals and debugging recipes |
