# pricing

## Description

Billing layer. Wraps Stripe Checkout, the Stripe Customer Portal, and the webhook pipeline that keeps
each user's subscription level in sync with Stripe. It also owns the point where the 7-day free trial
is cancelled once a user starts paying.

This app **does not decide permissions**. It resolves which `user_levels.Level` a Stripe subscription
maps to and writes it; every capability, limit, and downgrade consequence is handled by
`user_levels` (see [`apps/user_levels/README.md`](../user_levels/README.md)). It also sells
**add-ons** (paid tools on top of a plan) and records who bought them in `UserAddon`; each feature
app combines its capability with `user_has_addon` for its UI gate (e.g.
`client_area.user_has_client_area`).

Relationship to the core apps:

- **`users.User`** — holds `stripe_customer_id` and `allow_unpaid_subscription`; `StripeSubscriptionRecord`
  is a OneToOne extension.
- **`user_levels`** — reads `Level` / `LevelType` to map products to levels and calls
  `cancel_free_trial(user)` when an active paid subscription is detected.
- **`core`** — push notifications on subscription events and Redis helpers.

## Models and Data

### `StripeSubscriptionRecord`

OneToOne → `users.User`. Local mirror of the active Stripe subscription: subscription ID, price ID,
status, and period boundaries. Written by `upsert_subscription_record` and `mark_subscription_deleted`.
Tracks the **plan** subscription only; add-on subscriptions never touch it.

### Add-ons: `Addon`, `AddonPrice`, `UserAddon`

| Model | Purpose |
|---|---|
| `Addon` | Catalog entry. `code` matches the Stripe product metadata `addon_code`. `capability_model_key` + `capability_action` name the `user_levels` capability that already includes the tool (no charge for those levels). `is_active` = on sale. |
| `AddonPrice` | Monthly Stripe price per `(addon, level)`. A level without a row cannot buy the add-on. |
| `UserAddon` | Purchase state per `(user, addon)`: `is_active`, `stripe_subscription_id`, `stripe_item_id`. Written only from Stripe webhooks and reconciliation. |

Prices live in the database (admin → *Add-ons*), like plan prices on `Level`, so each environment
(sandbox, live) sets its own IDs without new settings.

### Free trial

The trial is stored on `user_levels.UserLevelProfile` (`free_trial_active`, `free_trial_ends_at`,
`free_trial_task_id`), not here. Lifecycle:

1. Users register at level **PRO**, gated by `InitialTrainingGateMiddleware`.
2. Completing the initial training calls `User.initial_training_completed()`, which triggers
   `user_levels.utils.activate_free_trial(user)`.
3. That sets `free_trial_active`, `free_trial_ends_at = now + 7 days`, and schedules the Celery task
   `user_levels.tasks.end_free_trial` with an `eta`.
4. After 7 days the task downgrades the user to **BASIC** and clears the trial fields.

`initial_training_done` guarantees the trial activates only once. If the user subscribes during the
trial, `sync_subscription_status()` calls `cancel_free_trial(user)`, which revokes the scheduled
Celery task and clears the fields — the purchased level stands.

Users who never finish the training are blocked by middleware and never receive a trial.

### Redis caches

| Key | Written by | TTL |
|---|---|---|
| `level_prices:<level_code>` | `get_level_prices_from_stripe` | 60 s |
| Stripe active-subscription flag per user | `_cache_stripe_active` | 24 h (`STRIPE_SUBSCRIPTION_ACTIVE_CACHE_TTL`) |

Invalidate with `level.invalidate_prices_cache()` or `invalidate_stripe_subscription_cache(user_id)`.

### Modules

| Module | Responsibility |
|---|---|
| `stripe_utils.py` | Stripe client, customer creation, checkout and portal sessions, subscription sync, plan-change detection, price and status caching |
| `utils.py` | Subscription lifecycle emails (created, upgraded, downgraded, cancelled) |
| `services/addons.py` | Add-on access checks, level price lookup, Stripe sync, and re-pricing |
| `signals.py` · `tasks.py` | Queue `reconcile_user_addons` when a user with add-ons changes level |
| `templatetags/addons.py` | `addon_code` filter: maps a `<code>_addon` alert key to its add-on |

Key functions in `stripe_utils.py`: `get_or_create_stripe_customer`, `create_checkout_session`,
`create_customer_portal_session`, `sync_subscription_status`, `subscription_addon_codes`,
`has_active_stripe_subscription`, `get_level_prices_from_stripe`, `get_plan_value`,
`detect_plan_change_type`, `apply_downgrade_at_period_end`,
`schedule_subscription_cancel_at_period_end`.

`schedule_subscription_cancel_at_period_end` sets `cancel_at_period_end=True` on billable
subscriptions (no refund, same as the Customer Portal). Missing or invalid customers and accounts
without a billable subscription are no-ops. A failed `modify` after retries raises
`StripeCancelAtPeriodEndError`.

## Views and Frontend Integration

**This app does not use HTMX.** The pricing page updates itself through a plain AJAX call to
`subscription_status`.

URL prefix: **`/pricing/`**

| URL | View | Response |
|---|---|---|
| `""` | `pricing_page` | Plan listing (HTML) |
| `checkout/<level_code>/<period>/` | `create_checkout` | 303 redirect to Stripe Checkout, or to the Customer Portal when a subscription is already active |
| `addon/<addon_code>/checkout/` | `create_addon_checkout` | POST (`next` = return path): Checkout of the add-on as its own subscription at the user's level price; redirects to `next` if already entitled or no price exists |
| `checkout/success/` · `checkout/cancel/` | `checkout_success`, `checkout_cancel` | Post-checkout pages |
| `portal/` | `customer_portal` | Redirect to a fresh Customer Portal session |
| `webhook/` | `stripe_webhook` | Signature-verified webhook receiver (`HttpResponse` 200/4xx/5xx) |
| `subscription/status/` | `subscription_status` | JSON: active level and billing period |

Dynamic UI behaviour: on load, the pricing page requests `subscription_status` and shows the
"Plan Actual" badge only when both the level **and** the selected period match. With an active
subscription, the current plan/period shows "Gestionar Suscripción"; every other button still reads
"Lo quiero" but redirects to the Customer Portal, which centralises plan changes and prevents
duplicate subscriptions.

## Configuration and Dependencies

### Settings

| Setting | Purpose |
|---|---|
| `STRIPE_API_KEY` | Publishable key (test or live) |
| `STRIPE_SECRET_KEY` | Secret key |
| `STRIPE_WEBHOOK_SECRET` | `whsec_…` signing secret used to verify webhook signatures |
| `REDIS_URL`, `REDIS_KEY_PREFIX` | Price and subscription-status caches |
| Email (SMTP) settings | Subscription lifecycle emails |

Stripe API version pinned by the integration: **2025-12-15**.

### Stripe Dashboard setup

**Subscriptions** — leave Checkout's *Limit customers to one subscription* **off**: the client-area
add-on is a second subscription. One **plan** subscription per customer is enforced in code
(`create_checkout` sends users with an active plan to the Customer Portal). Each platform user maps
to exactly one Stripe customer; `get_or_create_stripe_customer()` reuses `stripe_customer_id` or
creates a new customer with `user_id` / `username` metadata.

**Products and prices** — one product per paid level (PRO, LEADER, LEADER PRO), each with a monthly
and a yearly price. Every product **must** carry the metadata key `level_code` with value `pro`,
`leader`, or `leader_pro`; `sync_subscription_status()` uses it to map a Stripe subscription to a
platform level.

**Add-ons** — one Stripe product per add-on, **no** `level_code`, metadata `addon_code=<code>`,
with one monthly price per level that can buy it. Register each price in the admin as an
`AddonPrice`.

- **Always its own subscription.** The Customer Portal cannot change plans on multi-product
  subscriptions, and monthly add-ons cannot share a yearly plan subscription, so the plan
  subscription stays single-product.
- **Checkout** uses `get_addon_price_id(addon, user.level_code)`. The webhook **does not** change
  `Level`; it only writes `UserAddon`. `has_active_stripe_subscription` ignores add-on subscriptions.
- **Level changes** (plan webhook, trial expiry, admin) fire `pricing.signals`, which queues
  `reconcile_user_addons`. Billing changes always take effect at the **next renewal**, with no
  credits or immediate charges: a different level price is scheduled with `proration_behavior=none`,
  and if the new level's capability already includes the add-on the subscription is set to
  `cancel_at_period_end` (access continues until then; the capability covers it after that). With
  no price for the new level, the subscription is left unchanged and a warning is logged.
- Users with any add-on can open the Customer Portal to cancel it, even on Basic.

**Independence rule.** Plans and add-ons are separate Stripe subscriptions with separate
handlers:

| Event | Effect on the other side |
|---|---|
| Add-on bought, renewed, cancelled, or deleted | None: `Level`, `StripeSubscriptionRecord`, trial, and plan emails stay untouched (`sync_addon_subscription`, `_handle_addon_subscription_updated` / `_deleted`) |
| Plan checkout / portal / `has_active_stripe_subscription` / `subscription_status` | Only the subscription with a `level_code` item counts; add-on subscriptions are ignored |
| Level changes (plan webhook, trial expiry, admin) | Add-on billing changes at the **next period** only (`reconcile_user_addons`): new price with no proration, or `cancel_at_period_end` when the level already includes the tool. No credits or mid-cycle charges |

**Adding a new add-on:**

1. Stripe: create the product with `addon_code=<code>` and one monthly price per level.
2. `user_levels`: add the capability that includes it on the higher levels (`DEFAULT_LEVELS` +
   data migration), e.g. `{"<model_key>": {"access": {"allowed": true}}}`.
3. Admin → *Add-ons*: create the `Addon` (code, name, capability) and its `AddonPrice` rows.
4. Feature app: gate the UI with the capability **or** `user_has_addon(user, "<code>")`.
5. Lock screen: seed a `RestrictedAccessAlert` with key `<code>_addon`. `pro-locked-content.html`
   then renders the "Adquirir Herramienta" button posting to `create_addon_checkout`.

Plan price IDs are stored on `user_levels.Level`:

```python
from apps.user_levels.models import Level, LevelType

pro = Level.objects.get(code=LevelType.PRO)
pro.id_monthly_price_stripe = "price_xxxxx"
pro.id_yearly_price_stripe = "price_yyyyy"
pro.save()
```

**Webhook** — endpoint `https://<domain>/pricing/webhook/`. Events handled by `stripe_webhook`:

| Event | Effect |
|---|---|
| `checkout.session.completed` | Syncs the initial subscription |
| `customer.subscription.created` | Activates the corresponding level |
| `customer.subscription.updated` | Renewal, plan change, or scheduled cancellation |
| `customer.subscription.deleted` | Plan: downgrade to BASIC. Add-on: deactivates the `UserAddon`, leaves the level, and notifies unless the current level already includes it |
| `invoice.payment_succeeded` | Confirms the subscription is paid |
| `invoice.payment_failed` | Logged; Stripe retries automatically |
| `invoice.upcoming` | Renewal notice, 3 days ahead by default |
| `invoice.payment_action_required` | 3D Secure authentication notice |

> `customer.subscription.trial_will_end` is **not** handled: trial expiry is driven by the local
> Celery task, not by Stripe. Do not rely on it when configuring the endpoint.

**Customer Portal** (`settings/billing/portal`) — configure upgrades with proration
`Always invoice` and billing anchor `Update to new plan immediately`; downgrades and cancellations
with proration `None` (or `Credit for unused time`) and `Remain on current billing cycle`, effective
at period end with no automatic refunds. Portal sessions are single-use and expire after 5 minutes,
so a new one is created on every access.

### Plan-change detection

`customer.subscription.updated` compares the annualised value of the old and new price
(`get_plan_value`) to classify the change through `detect_plan_change_type`:

- **Upgrade** — applied immediately with proration.
- **Downgrade** — recorded by `apply_downgrade_at_period_end`; the user keeps the current level until
  the period ends.
- **Cancellation** — access retained until the paid period ends.

Each case sends a tailored push notification through `core.utils.notifications.push_notification`.

### Testing

Test cards: success `4242 4242 4242 4242`, declined `4000 0000 0000 0002`, 3D Secure
`4000 0025 0000 3155`.

Forward webhooks locally:

```bash
stripe listen --forward-to localhost:8000/pricing/webhook/
```

Scenarios worth covering: new subscription, monthly→yearly upgrade (immediate), LEADER→PRO downgrade
(level retained until period end), and cancellation (access until period end).

### Production checklist

1. Switch to live keys in the environment.
2. Recreate products and prices in live mode with the `level_code` metadata.
3. Register the live webhook endpoint and update `STRIPE_WEBHOOK_SECRET`.
4. Update the price IDs stored on `Level`.
5. Validate with a small real transaction.

Environment variables are injected per deployment environment; see
[`docs/docker.md`](../../docs/docker.md).

App dependencies: `core`, `user_levels`, `users`, `client_area`. External: Stripe, Redis, Celery
(`pricing.tasks.reconcile_user_addons`). No Sentry or Cloudflare usage of its own; the
trial-expiry task belongs to `user_levels`.
