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
| `ClientAccessRequest` | FK → perfil; primer acceso o continuidad. |

### Servicios

| Módulo | Responsabilidad |
|---|---|
| `services/access.py` | Asignación de código de acceso único. |
| `services/entitlement.py` | `user_has_client_area(user)` — capability **o** `user_has_addon(user, CLIENT_AREA_ADDON_CODE)`. |
| `services/programs.py` | Fecha de fin y ventana activa del programa. |

La pestaña del modal de contacto vive en `communication`. Básico/Pro bloqueados ven
`RestrictedAccessAlert` `client_area_addon`, cuyo botón hace POST a `create_addon_checkout`
con `client_area`. El URLConf sigue vacío; las herramientas HTMX y
`/api/client/` van en ramas siguientes.

## Configuración y dependencias

Dependencias: `communication`, `boards`, `users`, `user_levels`, `pricing`. Media por el backend
global. El catálogo de add-ons, sus precios por nivel y el checkout Stripe viven en `pricing`
(`Addon` con código `client_area`, sembrado por la migración `0003` de `pricing`).
Esta app **aún no usa** Sentry, Redis ni Celery.
