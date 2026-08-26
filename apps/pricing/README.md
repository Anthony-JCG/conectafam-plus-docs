# pricing

## Description

Billing layer. Wraps Stripe Checkout, the Stripe Customer Portal, and the webhook pipeline that keeps
each user's subscription level in sync with Stripe. It also owns the point where the 7-day free trial
is cancelled once a user starts paying.

This app **does not decide permissions**. It resolves which `user_levels.Level` a Stripe subscription
maps to and writes it; every capability, limit, and downgrade consequence is handled by
`user_levels` (see [`apps/user_levels/README.md`](../user_levels/README.md)).

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

Key functions in `stripe_utils.py`: `get_or_create_stripe_customer`, `create_checkout_session`,
`create_customer_portal_session`, `sync_subscription_status`, `has_active_stripe_subscription`,
`get_level_prices_from_stripe`, `get_plan_value`, `detect_plan_change_type`,
`apply_downgrade_at_period_end`.

## Views and Frontend Integration

**This app does not use HTMX.** The pricing page updates itself through a plain AJAX call to
`subscription_status`.

URL prefix: **`/pricing/`**

| URL | View | Response |
|---|---|---|
| `""` | `pricing_page` | Plan listing (HTML) |
| `checkout/<level_code>/<period>/` | `create_checkout` | 303 redirect to Stripe Checkout, or to the Customer Portal when a subscription is already active |
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

**Subscriptions** (`settings/billing/automatic`) must allow **one active subscription per customer**.
Each platform user maps to exactly one Stripe customer; `get_or_create_stripe_customer()` reuses
`stripe_customer_id` or creates a new customer with `user_id` / `username` metadata.

**Products and prices** — one product per paid level (PRO, LEADER, LEADER PRO), each with a monthly
and a yearly price. Every product **must** carry the metadata key `level_code` with value `pro`,
`leader`, or `leader_pro`; `sync_subscription_status()` uses it to map a Stripe subscription to a
platform level.

Price IDs are stored on `user_levels.Level`:

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
| `customer.subscription.deleted` | Downgrade to BASIC |
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

App dependencies: `core`, `user_levels`, `users`. External: Stripe, Redis. **No Sentry, Celery, or
Cloudflare usage of its own** — the trial-expiry Celery task belongs to `user_levels`.
