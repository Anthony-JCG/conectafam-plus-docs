# pricing

## Descripción

Capa de facturación. Envuelve Stripe Checkout, el Customer Portal de Stripe y el pipeline de
webhooks que mantiene el nivel de suscripción de cada usuario sincronizado con Stripe. También posee
el punto en el que se cancela la prueba gratuita de 7 días cuando un usuario empieza a pagar.

Esta app **no decide permisos**. Resuelve a qué `user_levels.Level` mapea una suscripción Stripe y
lo escribe; cada capability, límite y consecuencia de degradación lo gestiona `user_levels` (véase
[`apps/user_levels/README.es.md`](../user_levels/README.es.md)). También vende **add-ons**
(herramientas de pago sobre un plan) y registra quién los compró en `UserAddon`; cada app de
funcionalidad combina su capability con `user_has_addon` para su puerta de UI (p. ej.
`client_area.user_has_client_area`).

Relación con las apps núcleo:

- **`users.User`** — mantiene `stripe_customer_id` y `allow_unpaid_subscription`;
  `StripeSubscriptionRecord` es una extensión OneToOne.
- **`user_levels`** — lee `Level` / `LevelType` para mapear productos a niveles y llama a
  `cancel_free_trial(user)` cuando detecta una suscripción de pago activa.
- **`core`** — notificaciones push en eventos de suscripción y helpers de Redis.

## Modelos y datos

### `StripeSubscriptionRecord`

OneToOne → `users.User`. Espejo local de la suscripción Stripe activa: ID de suscripción, ID de
precio, estado y límites del periodo. Escrito por `upsert_subscription_record` y
`mark_subscription_deleted`. Solo sigue la suscripción **de plan**; las de add-ons nunca lo tocan.

### Add-ons: `Addon`, `AddonPrice`, `UserAddon`

| Modelo | Propósito |
|---|---|
| `Addon` | Entrada del catálogo. `code` coincide con el metadato `addon_code` del producto Stripe. `capability_model_key` + `capability_action` nombran la capability de `user_levels` que ya incluye la herramienta (esos niveles no pagan). `is_active` = a la venta. |
| `AddonPrice` | Precio mensual de Stripe por `(addon, nivel)`. Un nivel sin fila no puede comprar el add-on. |
| `UserAddon` | Estado de compra por `(usuario, addon)`: `is_active`, `stripe_subscription_id`, `stripe_item_id`. Solo lo escriben los webhooks de Stripe y la reconciliación. |

Los precios viven en la base de datos (admin → *Add-ons*), igual que los de plan en `Level`, así
cada entorno (sandbox, live) pone sus propios IDs sin settings nuevos.

### Prueba gratuita

La prueba se almacena en `user_levels.UserLevelProfile` (`free_trial_active`, `free_trial_ends_at`,
`free_trial_task_id`), no aquí. Ciclo de vida:

1. Los usuarios se registran en el nivel **PRO**, controlados por `InitialTrainingGateMiddleware`.
2. Completar la formación inicial llama a `User.initial_training_completed()`, que dispara
   `user_levels.utils.activate_free_trial(user)`.
3. Eso establece `free_trial_active`, `free_trial_ends_at = now + 7 days` y programa la tarea Celery
   `user_levels.tasks.end_free_trial` con un `eta`.
4. Tras 7 días la tarea degrada al usuario a **BASIC** y limpia los campos de la prueba.

`initial_training_done` garantiza que la prueba se activa solo una vez. Si el usuario se suscribe
durante la prueba, `sync_subscription_status()` llama a `cancel_free_trial(user)`, que revoca la
tarea Celery programada y limpia los campos — prevalece el nivel comprado.

Los usuarios que nunca terminan la formación quedan bloqueados por el middleware y nunca reciben
prueba.

### Cachés Redis

| Clave | Escrita por | TTL |
|---|---|---|
| `level_prices:<level_code>` | `get_level_prices_from_stripe` | 60 s |
| Flag de suscripción activa Stripe por usuario | `_cache_stripe_active` | 24 h (`STRIPE_SUBSCRIPTION_ACTIVE_CACHE_TTL`) |

Invalidar con `level.invalidate_prices_cache()` o `invalidate_stripe_subscription_cache(user_id)`.

### Módulos

| Módulo | Responsabilidad |
|---|---|
| `stripe_utils.py` | Cliente Stripe, creación de customer, sesiones de checkout y portal, sincronización de suscripción, detección de cambio de plan, caché de precios y estado |
| `utils.py` | Emails del ciclo de vida de suscripción (creada, ascendida, degradada, cancelada) |
| `services/addons.py` | Comprobación de acceso, precio por nivel, sincronización con Stripe y re-precio de add-ons |
| `signals.py` · `tasks.py` | Encolan `reconcile_user_addons` cuando un usuario con add-ons cambia de nivel |
| `templatetags/addons.py` | Filtro `addon_code`: convierte una clave de alerta `<code>_addon` en su add-on |

Funciones clave en `stripe_utils.py`: `get_or_create_stripe_customer`, `create_checkout_session`,
`create_customer_portal_session`, `sync_subscription_status`, `subscription_addon_codes`,
`has_active_stripe_subscription`, `get_level_prices_from_stripe`, `get_plan_value`,
`detect_plan_change_type`, `apply_downgrade_at_period_end`,
`schedule_subscription_cancel_at_period_end`.

`schedule_subscription_cancel_at_period_end` marca `cancel_at_period_end=True` en las suscripciones
facturables (sin reembolso, igual que el Customer Portal). Customer ausente o inválido y cuentas
sin suscripción facturable son no-ops. Un `modify` fallido tras reintentos lanza
`StripeCancelAtPeriodEndError`.

## Vistas e integración frontend

**Esta app no usa HTMX.** La página de precios se actualiza con una llamada AJAX sencilla a
`subscription_status`.

Prefijo de URL: **`/pricing/`**

| URL | Vista | Respuesta |
|---|---|---|
| `""` | `pricing_page` | Listado de planes (HTML) |
| `checkout/<level_code>/<period>/` | `create_checkout` | Redirección 303 a Stripe Checkout, o al Customer Portal cuando ya hay una suscripción activa |
| `addon/<addon_code>/checkout/` | `create_addon_checkout` | POST (`next` = ruta de vuelta): Checkout del add-on como suscripción propia al precio del nivel del usuario; vuelve a `next` si ya tiene acceso o no hay precio |
| `checkout/success/` · `checkout/cancel/` | `checkout_success`, `checkout_cancel` | Páginas posteriores al checkout |
| `portal/` | `customer_portal` | Redirección a una sesión nueva del Customer Portal |
| `webhook/` | `stripe_webhook` | Receptor de webhooks con verificación de firma (`HttpResponse` 200/4xx/5xx) |
| `subscription/status/` | `subscription_status` | JSON: nivel activo y periodo de facturación |

Comportamiento dinámico de la UI: al cargar, la página de precios solicita `subscription_status` y
muestra la insignia «Plan Actual» solo cuando coinciden tanto el nivel **como** el periodo
seleccionado. Con una suscripción activa, el plan/periodo actual muestra «Gestionar Suscripción»;
el resto de botones siguen leyendo «Lo quiero» pero redirigen al Customer Portal, que centraliza los
cambios de plan y evita suscripciones duplicadas.

## Configuración y dependencias

### Ajustes

| Setting | Propósito |
|---|---|
| `STRIPE_API_KEY` | Clave publicable (test o live) |
| `STRIPE_SECRET_KEY` | Clave secreta |
| `STRIPE_WEBHOOK_SECRET` | Secreto de firma `whsec_…` usado para verificar firmas de webhook |
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Cachés de precios y de estado de suscripción |
| Ajustes de email (SMTP) | Emails del ciclo de vida de suscripción |

Versión de la API Stripe fijada por la integración: **2025-12-15**.

### Configuración del Stripe Dashboard

**Subscriptions** — dejar **desactivado** *Limit customers to one subscription* de Checkout: el
add-on de Área de clientes es una segunda suscripción. Una sola suscripción **de plan** por
customer se garantiza en código (`create_checkout` manda al Customer Portal si ya hay plan activo).
Cada usuario de la plataforma mapea a exactamente un customer de Stripe;
`get_or_create_stripe_customer()` reutiliza `stripe_customer_id` o crea un customer nuevo con
metadatos `user_id` / `username`.

**Products and prices** — un producto por nivel de pago (PRO, LEADER, LEADER PRO), cada uno con un
precio mensual y uno anual. Cada producto **debe** llevar la clave de metadatos `level_code` con
valor `pro`, `leader` o `leader_pro`; `sync_subscription_status()` la usa para mapear una
suscripción Stripe a un nivel de la plataforma.

**Add-ons** — un producto Stripe por add-on, **sin** `level_code`, metadato `addon_code=<code>`,
con un precio mensual por cada nivel que pueda comprarlo. Cada precio se registra en el admin como
`AddonPrice`.

- **Siempre es una suscripción propia.** El Customer Portal no permite cambiar de plan en
  suscripciones con varios productos, y un add-on mensual no puede convivir con un plan anual en la
  misma suscripción; por eso la suscripción de plan sigue teniendo un solo producto.
- **Checkout** usa `get_addon_price_id(addon, user.level_code)`. El webhook **no** cambia el
  `Level`; solo escribe `UserAddon`. `has_active_stripe_subscription` ignora las suscripciones de
  add-ons.
- **Cambios de nivel** (webhook de plan, fin de prueba, admin) disparan `pricing.signals`, que
  encola `reconcile_user_addons`. Los cambios de cobro aplican siempre en la **próxima renovación**,
  sin créditos ni cargos inmediatos: un precio distinto de nivel se programa con
  `proration_behavior=none`, y si la capability del nuevo nivel ya incluye el add-on la suscripción
  queda en `cancel_at_period_end` (el acceso sigue hasta entonces; luego lo cubre la capability).
  Si el nuevo nivel no tiene precio, la suscripción no se toca y se registra un warning.
- Quien tenga cualquier add-on puede abrir el Customer Portal para cancelarlo, aunque sea Básico.

**Regla de independencia.** Planes y add-ons son suscripciones Stripe separadas con manejadores
separados:

| Evento | Efecto en el otro lado |
|---|---|
| Add-on comprado, renovado, cancelado o eliminado | Ninguno: `Level`, `StripeSubscriptionRecord`, prueba gratuita y emails de plan no se tocan (`sync_addon_subscription`, `_handle_addon_subscription_updated` / `_deleted`) |
| Checkout de plan / portal / `has_active_stripe_subscription` / `subscription_status` | Solo cuenta la suscripción con ítem `level_code`; las de add-ons se ignoran |
| Cambio de nivel (webhook de plan, fin de prueba, admin) | El cobro del add-on cambia solo en el **próximo periodo** (`reconcile_user_addons`): nuevo precio sin prorrateo, o `cancel_at_period_end` si el nivel ya incluye la herramienta. Sin créditos ni cargos a mitad de ciclo |

**Añadir un add-on nuevo:**

1. Stripe: crear el producto con `addon_code=<code>` y un precio mensual por nivel.
2. `user_levels`: añadir la capability que lo incluye en los niveles altos (`DEFAULT_LEVELS` +
   migración de datos), p. ej. `{"<model_key>": {"access": {"allowed": true}}}`.
3. Admin → *Add-ons*: crear el `Addon` (código, nombre, capability) y sus filas `AddonPrice`.
4. App de la funcionalidad: proteger la UI con la capability **o** `user_has_addon(user, "<code>")`.
5. Pantalla de bloqueo: sembrar un `RestrictedAccessAlert` con clave `<code>_addon`;
   `pro-locked-content.html` pinta el botón «Adquirir Herramienta» que hace POST a
   `create_addon_checkout`.

Los IDs de precio de plan se almacenan en `user_levels.Level`:

```python
from apps.user_levels.models import Level, LevelType

pro = Level.objects.get(code=LevelType.PRO)
pro.id_monthly_price_stripe = "price_xxxxx"
pro.id_yearly_price_stripe = "price_yyyyy"
pro.save()
```

**Webhook** — endpoint `https://<domain>/pricing/webhook/`. Eventos gestionados por
`stripe_webhook`:

| Evento | Efecto |
|---|---|
| `checkout.session.completed` | Sincroniza la suscripción inicial |
| `customer.subscription.created` | Activa el nivel correspondiente |
| `customer.subscription.updated` | Renovación, cambio de plan o cancelación programada |
| `customer.subscription.deleted` | Plan: degradación a BASIC. Add-on: desactiva el `UserAddon`, no toca el nivel y avisa salvo que el nivel actual ya lo incluya |
| `invoice.payment_succeeded` | Confirma que la suscripción está pagada |
| `invoice.payment_failed` | Registrado; Stripe reintenta automáticamente |
| `invoice.upcoming` | Aviso de renovación, 3 días antes por defecto |
| `invoice.payment_action_required` | Aviso de autenticación 3D Secure |

> `customer.subscription.trial_will_end` **no** se gestiona: la caducidad de la prueba la impulsa la
> tarea Celery local, no Stripe. No dependas de él al configurar el endpoint.

**Customer Portal** (`settings/billing/portal`) — configura ascensos con prorrateo
`Always invoice` y ancla de facturación `Update to new plan immediately`; degradaciones y
cancelaciones con prorrateo `None` (o `Credit for unused time`) y `Remain on current billing cycle`,
efectivos al final del periodo sin reembolsos automáticos. Las sesiones del portal son de un solo
uso y caducan a los 5 minutos, así que se crea una nueva en cada acceso.

### Detección de cambio de plan

`customer.subscription.updated` compara el valor anualizado del precio antiguo y el nuevo
(`get_plan_value`) para clasificar el cambio mediante `detect_plan_change_type`:

- **Ascenso** — aplicado de inmediato con prorrateo.
- **Degradación** — registrada por `apply_downgrade_at_period_end`; el usuario conserva el nivel
  actual hasta que termine el periodo.
- **Cancelación** — el acceso se mantiene hasta que termine el periodo pagado.

Cada caso envía una notificación push adaptada a través de
`core.utils.notifications.push_notification`.

### Pruebas

Tarjetas de prueba: éxito `4242 4242 4242 4242`, rechazada `4000 0000 0000 0002`, 3D Secure
`4000 0025 0000 3155`.

Reenviar webhooks en local:

```bash
stripe listen --forward-to localhost:8000/pricing/webhook/
```

Escenarios que conviene cubrir: nueva suscripción, ascenso mensual→anual (inmediato), degradación
LEADER→PRO (nivel retenido hasta fin de periodo) y cancelación (acceso hasta fin de periodo).

### Checklist de producción

1. Cambiar a claves live en el entorno.
2. Recrear productos y precios en modo live con el metadato `level_code`.
3. Registrar el endpoint de webhook live y actualizar `STRIPE_WEBHOOK_SECRET`.
4. Actualizar los IDs de precio almacenados en `Level`.
5. Validar con una transacción real pequeña.

Las variables de entorno se inyectan por entorno de despliegue; véase
[`docs/docker.es.md`](../../docs/docker.es.md).

Dependencias de apps: `core`, `user_levels`, `users`, `client_area`. Externas: Stripe, Redis,
Celery (`pricing.tasks.reconcile_user_addons`). Sin uso propio de Sentry ni Cloudflare; la
tarea de caducidad de la prueba pertenece a `user_levels`.
