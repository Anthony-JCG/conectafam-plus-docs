# users

## Description

Owner of `users.User`, the custom user model that is the axis of the entire ecosystem. Every other
app hangs off it, either through a direct FK or through the self-referential `sponsor` FK that builds
the MLM sponsor tree.

Responsibilities: authentication, invitation-based registration, email verification, admin two-factor
authentication, multi-account browser sessions, and the middleware stack that gates the whole site
(login requirement, initial-training gate, activity tracking, timezone).

Relationship to the core apps:

- **`user_levels`** — reads the user's level through `UserLevelProfile`. Most level-related
  properties on `User` (`level_code`, `is_leader()`, `has_subscription`, `was_downgraded`) are thin
  accessors that delegate to `user_levels`; the rules themselves are never implemented here.
- **`core`** — notification helpers and shared constants.
- **`communication`** — bidirectional: `User.contact` is a OneToOne to `communication.Contact`, while
  `Contact.user` points back to `User`. A user registered from a contact keeps both records in sync
  through `User.save()`.

## Models and Data

### `User`

Extends `AbstractBaseUser` + `PermissionsMixin`. `USERNAME_FIELD = "username"`.

| Field | Type | Notes |
|---|---|---|
| `sponsor` | FK → `self` (`SET_NULL`) | Sponsor tree; traversed by `user_levels` |
| `contact` | OneToOne → `communication.Contact` (`SET_NULL`) | Origin contact when registered from the CRM |
| `username` | Char, unique | Login identifier |
| `email` | Email, unique | Also used for verification and password reset |
| `number_farmasi_influencer` | Char | Required business identifier |
| `token` | Char, nullable | Invitation token, produced by `generate_token()` |
| `name`, `phone`, `country`, `date_of_birth`, `profile_image`, `calendar_link` | — | Profile |
| `email_status`, `email_code` | — | Email verification state |
| `initial_training_done` | bool | Consumed by `InitialTrainingGateMiddleware` |
| `is_active`, `is_staff`, `is_admin` | bool | Technical flags |
| `registered_at`, `last_activity` | datetime | Registration and activity tracking |
| `from_contact` | bool | Registration origin |
| `stripe_customer_id` | Char, nullable | Set by `pricing` |
| `allow_unpaid_subscription` | bool | Courtesy accounts exempt from billing checks |

`UserManager.create_user` generates a temporary `username` when none is given, plus `email_code` and
the invitation token. `create_superuser` additionally requires `is_staff` and `is_admin`.

`save()` reprocesses `profile_image` (WebP, via `core.utils.files`) and pushes profile changes down to
the linked `Contact`.

Notable properties and methods — several resolve data from other apps through **lazy imports** to
avoid circular dependencies: `level_code`, `level_name`, `initial_level_name`, `was_downgraded`,
`was_leader_when_downgraded`, `has_subscription`, `has_free_trial`, `get_end_trial_time()`,
`show_subscription_correction_banner` (`user_levels`, `pricing`); `initial_training_completed()`,
`get_training_stats_data()`, `answered_input_training_fields` (`training`); `get_daily_progress()`,
`get_all_challenges_daily_progress()` (`challenge`); `get_users_invited()` (direct children in the
sponsor tree); `is_leader()`, `is_leader_pro()`, `is_any_leader()`, `registered_since`,
`generate_token()`.

### `BrowserAccountRegistry`

FK → `User`. One row per account registered in a browser, enabling the multi-account switcher.

### `VerificationCode`

FK → `User`. Short-lived codes for admin two-factor authentication.

## Views and Frontend Integration

**This app does not use HTMX.** Every view returns a full HTML page or a redirect; there are no JSON
endpoints and no partial fragments.

Routes are mounted at the project root (`Platform/urls.py` includes `apps.users.urls` under `""`),
which is why they own top-level paths such as `/login/`.

| View | URL | Purpose |
|---|---|---|
| `sing_in` | `login/` | Login |
| `register` | `<username>/register/<token>/` | Invitation-token registration |
| `register_sponsor_link` | `<username>/register/` | Public registration through a sponsor link |
| `email_validation` | `email-validation/` | Pending-verification screen |
| `email_confirmation` | `email-confirmation/<user_id>/<code>/` | Confirms the address |
| `log_out` | `logout/` | Logout, multi-account aware |
| `send_verification_code` / `verify_code` | `send-verification-code/`, `verify-code/` | Admin 2FA |
| `personal_link_mate` | `<username>_link/` | **Public Link Mate page**; renders data owned by `links` |
| `add_account`, `switch_account`, `remove_account_view`, `logout_all_accounts` | `accounts/…` | Multi-account session management |

Password reset uses `django.contrib.auth.views` with project templates
(`forgot-password.html`, `reset-password/…`) and custom forms `PasswordResetCustomForm` /
`SetPasswordCustomForm`.

### Middleware

All are registered in `settings.MIDDLEWARE`, in this order.

| Class | Purpose |
|---|---|
| `TimezoneFromSessionMiddleware` | Activates the timezone stored in `session["django_timezone"]` |
| `AccountRegistryMiddleware` | Keeps the active session recorded in the `account_registry` cookie |
| `TwoFactorAuthMiddleware` | Email 2FA for `/admin/`; **skipped when `DEBUG` is on** |
| `LoginRequiredMiddleware` | Requires authentication for app prefixes; exceptions declared in `public_routes.py` |
| `InitialTrainingGateMiddleware` | Redirects to `/training/onboarding/` until `initial_training_done` |
| `UpdateLastActivityMiddleware` | Refreshes `last_activity` at most once every 24 h |

## Configuration and Dependencies

| Setting | Purpose |
|---|---|
| `AUTH_USER_MODEL = "users.User"` | Referenced by every app in the project |
| `RECAPTCHA_PUBLIC_KEY`, `RECAPTCHA_PRIVATE_KEY` | `django-recaptcha` on registration and login forms |
| `EMAIL_HOST_PASSWORD` and SMTP settings | Verification, invitation, and password-reset email (console backend when `DEBUG`) |
| `DEBUG` | Disables admin 2FA in development |

There is **no `AUTHENTICATION_BACKENDS` entry**, so Django's default `ModelBackend` applies. The
multi-account service stores `BACKEND_SESSION_KEY` explicitly when switching accounts. The mobile API
authenticates separately with its own token scheme (see
[`apps/keyboard_api/README.md`](../keyboard_api/README.md)).

Supporting modules:

| Module | Responsibility |
|---|---|
| `services/multi_account.py` | Browser-level account registry, switching, removal |
| `utils.py` | Email dispatch through Celery, `redirect_authenticated_user` decorator, registration URL builders |
| `public_routes.py` | Regex list of routes exempt from `LoginRequiredMiddleware` |
| `context_processor.py` | Injects `saved_accounts` into every template |
| `tasks.py` | `send_email_task` (Celery) |

App dependencies: `communication`, `core`, `main`, `user_levels`, and lazy imports of `training`,
`challenge`, `pricing`, `links`. External: Celery (email), Redis (indirect, through `core`).
This app has **no direct Sentry or Cloudflare integration**; profile images go through
`core.utils.files` and therefore land on the storage backend configured globally.

> **This app defines no signals.** `signals.py` used to exist but was never imported — `apps.py` has
> no `ready()` hook — so its three receivers never ran, and all three were redundant: `Task` already
> cascades from `Challenge` and `Incentive` via `on_delete=CASCADE`, and the `main` caches it tried
> to clear are invalidated where it matters by `training.signals` and `training.views`. Level, sponsor
> and profile invalidation for `User` lives in `user_levels/signals.py`.
