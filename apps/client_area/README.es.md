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
| `ClientProgramAssignment` | FK → `ClientProfile`; FK opcional → `AcademyPlan`. Inicio y duración (la fecha de fin se calcula, no se guarda), academia, `academy_unlock_mode` (`all` = Siempre, `drip` = Por días; un único modo para toda la academia). |
| `ClientProgramFolder` | FK → asignación + `boards.BoardFolder`. |
| `ClientProgramFile` | FK → asignación; hueco nutrición/deporte/otros; `BoardItem` o archivo. |
| `ClientProduct` | FK → asignación; fecha, productos, observaciones. |
| `ClientLesson` | FK → asignación; copia del ítem de plan + `unlock_day`. |
| `ClientMeasurement` | FK → perfil; métricas; `source=client\|advisor`; `hidden_by_advisor` oculta la fila solo en la web. |
| `ClientProgressPhoto` | FK → perfil; frente/espalda/lado; `hidden_by_advisor` (solo web). |
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
- Academia: interruptor No/Sí, contenido disponible (Siempre / Por días), tarjetas de carpetas, contenidos por día, plantillas y copia de otro cliente.
- Progreso: fecha de inicio y duración elegidas por el asesor, fecha de fin calculada, activar (activa también el acceso a la app), %; al desactivar o expirar, el acceso vuelve a `none` y se crea una nota para el asesor.

### Servicios adicionales

| Modulo | Responsabilidad |
|---|---|
| services/profiles.py | get_or_create_client_profile |
| services/access_actions.py | Aceptar solicitud / activar / desactivar / dar acceso al activar el programa / quitarlo al terminar |
| services/content.py | Mediciones, fotos, archivos de programa, productos |
| services/academy.py | Ajustes (No/Sí + contenido disponible), carpetas, lecciones, plantillas, copia entre clientes |
| services/catalog.py | Busqueda del catalogo client-area |
| services/pane.py | Contexto del partial de herramientas |
| services/expiry.py | Expiracion diaria de programas + push web al asesor |
| 	asks.py | Celery expire_client_programs_task (beat 05:15) |

La API nativa (Fam Fit) comienza en `apps/client_api`; FCM al consumidor en ramas posteriores.

## Pulido WEB (Rama 6)

- Tablas de evolución y fotos con scroll horizontal (~4 columnas visibles). El asesor puede añadir filas y eliminar cualquiera, la haya registrado el cliente o el asesor. Eliminar solo marca `hidden_by_advisor`: la fila desaparece del panel web, pero la API de Fam Fit (`/api/client/`) la sigue devolviendo. No se puede deshacer.
- Las filas de evolución, fotos, archivos de programa y productos nutricionales se añaden con un botón **Añadir** que
  abre el modal compartido `#clientAreaFormModal` (`components/modals/client-area-modals.html`, incluido en
  `contacts.html` fuera de `#contactModal` para que se apile bien, junto al selector de catálogo). El botón lo abre
  con `Modal.show()` (`data-ca-open-form`), no con `data-bs-toggle`, que cerraría `#contactModal`.
  `client_area_tool_form` (`forms/<kind>/`) carga el formulario desde `views.TOOL_FORMS`; si se guarda bien, la vista
  reemplaza solo el parcial de esa tabla (`components/partials/client-area-*-table.html`) y envía `showToast` +
  `clientAreaFormSaved` (cierra el modal). Si hay errores, el formulario se vuelve a pintar dentro del modal
  (`HX-Retarget`). El modal extiende el global `base-modal.html` (`client-area-form-modal.html`); el parcial del
  formulario (`components/partials/client-area-tool-form.html`) rellena su cuerpo y fija el título con
  `hx-swap-oob`. Componentes cotton: `form_field`, `tool_add_button`.
- **Academia** (`components/partials/client-area-academy.html`): el interruptor No/Sí y **Contenido disponible**
  (`Siempre` = `all`, todas las lecciones abiertas; `Por días` = `drip`, cada lección se abre el día `unlock_day` del
  programa) se guardan al cambiarlos (`client_area_toggle_academy`). Las carpetas del catálogo
  se muestran como tarjetas seleccionables y también se guardan al marcarlas. Solo se vuelve a pintar esa sección.
  **Añadir contenido** abre el modal compartido con `ClientLessonForm` (kind `lesson`) y, al guardar, reemplaza solo la
  tabla de contenidos. Las plantillas y la copia desde otro cliente están en el desplegable **Plantillas**.
- **Progreso** (`components/partials/client-area-progress.html`): el asesor elige la fecha de inicio y la duración
  (`ProgramPeriodForm`). La fecha de fin no se puede editar: `client_area_tools.js` la recalcula al momento y el
  servidor nunca la recibe, porque siempre se deriva de inicio + duración (`program_end_date`). Por eso no hay campo en
  base de datos; la API de Fam Fit mantiene sus campos y añade `start_date` al bloque `program`. Mientras el programa
  no ha empezado, el botón es **Activar**; después aparecen **Guardar** (cambia inicio y duración) y **Desactivar**.
  Si el formulario no es válido, se vuelve a pintar la sección con los errores. Títulos, campos y botones usan los
  tamaños compactos del resto del panel.
- **Programa y acceso a la app**: `activate_program` llama a `access_actions.grant_access_for_program`, que acepta las
  solicitudes de acceso pendientes (primer acceso o continuidad) o, si no hay ninguna, activa el perfil. Así el cliente
  puede entrar en Fam Fit con `access_code` + `device_id`. Tanto `deactivate_program` como la expiración diaria llaman
  a `clear_access_on_program_end`, que deja el acceso en `none` ("Sin acceso"); cuando el cliente vuelva a entrar con
  su código se creará una nueva solicitud `first_access` para el asesor.
- Tarjeta **Solicitudes** en el home (junto a tareas programadas): Admitir, WhatsApp, Ver todas.
- Listado: `client_area_access_requests`.
- `activate_program` / `deactivate_program` escriben `ActivityContact` (la expiración automática ya lo hacía al finalizar).

