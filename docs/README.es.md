# Documentación

Documentación de infraestructura y operaciones de Impact Tech. Son **guías temáticas y
runbooks**: cómo se despliega, opera y depura el sistema.

La referencia a nivel de aplicación — modelos, servicios, endpoints, reglas de acceso — no está
aquí. Vive junto al código, en el `README.md` de cada app. El [README raíz](../README.es.md) las
indexa todas.

| Documento | Contenido |
|---|---|
| [docker.es.md](docker.es.md) | Arquitectura de contenedores, los tres entornos, Nginx, entrypoint, volúmenes y CI/CD |
| [backups.es.md](backups.es.md) | Dump nocturno de MySQL a Cloudflare R2: instalación, retención y procedimiento de restauración |
| [user-levels-cache.es.md](user-levels-cache.es.md) | Caché Redis detrás de `user_levels`: claves, TTL, señales de invalidación y recetas de depuración |
