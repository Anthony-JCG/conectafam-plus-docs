# client_area

**Área de clientes** del asesor: programas de nutrición/deporte, códigos de acceso, medidas,
planes de academia y (más adelante) la API de la app nativa. El consumidor es un `ClientProfile`
ligado a un `communication.Contact`, no un `users.User` del árbol de patrocinio.

Relación con las apps núcleo:

- **`user_levels`** — `CLIENT_AREA_MODEL_KEY` + `ACCESS_ACTION_KEY`. Líder y Líder Pro permitidos.
  Básico/Pro denegados ahí; `user_has_client_area` también acepta el add-on `client_area`
  comprado (`pricing.UserAddon`).
- **`communication`** — `ClientProfile.contact` es OneToOne a `Contact`. Las notas de alta/baja
  del programa escribirán `ActivityContact`.
- **`boards`** — el catálogo y las carpetas de academia apuntan a `BoardItem` / `BoardFolder`.
- **`users.User`** — el asesor posee `AcademyPlan`. El cliente nunca es este usuario.

## Modelos y datos

| Modelo | Relaciones |
|---|---|
| `ClientProfile` | OneToOne → `communication.Contact`. `access_code` único. Estado de acceso. Sin FK a User (tokens de dispositivo con la API). |
| `AcademyPlan` | FK → `users.User` (asesor). Conjunto de lecciones reutilizable. |
| `AcademyPlanItem` | FK → `AcademyPlan`; FK opcional → `boards.BoardItem`; `unlock_day`. |
| `ClientProgramAssignment` | FK → `ClientProfile`; FK opcional → `AcademyPlan`. Inicio, duración, academia, drip vs todo. |
| `ClientProgramFolder` | FK → asignación + `boards.BoardFolder`. |
| `ClientProgramFile` | FK → asignación; hueco nutrición/deporte/otros; `BoardItem` o archivo. |
| `ClientProduct` | FK → asignación; fecha, productos, observaciones. |
| `ClientLesson` | FK → asignación; copia del ítem de plan + `unlock_day`. |
| `ClientMeasurement` | FK → perfil; métricas; `source=client\|advisor`. El asesor no borra `source=client`. |
| `ClientProgressPhoto` | FK → perfil; frente/espalda/lado. |
| `ClientAccessRequest` | FK → perfil; primer acceso o continuidad; `order_number` / `purchase_date` opcionales. |

### Servicios

| Módulo | Responsabilidad |
|---|---|
| `services/access.py` | Asignación de código de acceso único. |
| `services/entitlement.py` | `user_has_client_area(user)` — capability **o** `user_has_addon(user, CLIENT_AREA_ADDON_CODE)`. |
| `services/programs.py` | Fecha de fin, ventana activa, estado en tarjeta y filtro de lista. |

La pestaña del modal de contacto vive en `communication`. Básico/Pro bloqueados ven
`RestrictedAccessAlert` `client_area_addon`, cuyo botón hace POST a `create_addon_checkout`
con `client_area`. Con entitlement, `#pane-cliente` carga por HTMX `load_client_area_pane`
(`/client-area/load-pane/`) con el esqueleto de secciones; las herramientas completas llegan en
ramas siguientes. Las tarjetas de contacto muestran activo/inactivo del programa desde
`services/programs.py` (no el `membership` del CRM). `/api/client/` está en `apps/client_api` (app nativa Fam Fit).

## Configuración y dependencias

Dependencias: `communication`, `boards`, `users`, `user_levels`, `pricing`. Media por el backend
global. El catálogo de add-ons, sus precios por nivel y el checkout Stripe viven en `pricing`
(`Addon` con código `client_area`, sembrado por la migración `0003` de `pricing`).
Esta app **aún no usa** Sentry, Redis ni Celery.

## Catálogo (boards)

El catálogo compartido de FAM TEAM es un `boards.Board` con `is_client_area=True`,
sembrado con `python manage.py seed_client_area_board` (carpetas: Nutrición, Deporte,
Videoteca, Otros). Los asesores con `user_has_client_area` lo abren en solo lectura y
eligen referencias `BoardItem` / `BoardFolder` para programas. No pueden editar el
contenido de sistema; sus archivos personales van en sus boards o en
`ClientProgramFile`. Ver el README de `apps/boards`.


## Herramientas WEB (modal de contacto)

Con entitlement, #pane-cliente carga por HTMX el partial completo client-area-tools:

- Badges App Store / Play Store (placeholders hasta que existan URLs en settings).
- Codigo de acceso con copiar; aceptar solicitud; activar / desactivar acceso.
- Enlace WhatsApp (wa.me) si el contacto tiene telefono.
- Tablas: evolucion (asesor anade filas), fotos, programa (PDF alimentacion/deporte/otros), productos.
- Selector de catalogo FAM TEAM (Board.is_client_area) con mosaico + busqueda Redis (search_index filtrado).
- Academia: interruptor, chips de carpetas, lecciones por dia, guardar / reutilizar plantilla, copiar de otro cliente.
- Progreso: dias, fecha fin, activar, %; al expirar el acceso pasa a 
one y se crea nota de asesor.

### Servicios adicionales

| Modulo | Responsabilidad |
|---|---|
| services/profiles.py | get_or_create_client_profile |
| services/access_actions.py | Aceptar solicitud / activar / desactivar / limpiar en expiracion |
| services/content.py | Mediciones, fotos, archivos de programa, productos |
| services/academy.py | Toggle, carpetas, lecciones, plantillas, copia entre clientes |
| services/catalog.py | Busqueda del catalogo client-area |
| services/pane.py | Contexto del partial de herramientas |
| services/expiry.py | Expiracion diaria de programas + push web al asesor |
| 	asks.py | Celery expire_client_programs_task (beat 05:15) |

La API nativa (Fam Fit) comienza en `apps/client_api`; FCM al consumidor en ramas posteriores.

## Pulido WEB (Rama 6)

- Tablas de evolución y fotos con scroll horizontal (~4 columnas visibles). El asesor puede añadir y borrar solo filas con `source=advisor` (no borra `source=client`).
- Tarjeta **Solicitudes** en el home (junto a tareas programadas): Admitir, WhatsApp, Ver todas.
- Listado: `client_area_access_requests`.
- `activate_program` / `deactivate_program` escriben `ActivityContact` (la expiración automática ya lo hacía al finalizar).

