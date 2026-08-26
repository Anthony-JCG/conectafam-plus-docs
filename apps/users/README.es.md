# users

## Descripción

Dueña de `users.User`, el modelo de usuario personalizado que es el eje de todo el ecosistema. El
resto de apps se engancha a él, ya sea por una FK directa o por la FK autorreferencial `sponsor` que
construye el árbol de patrocinio MLM.

Responsabilidades: autenticación, registro por invitación, verificación de email, autenticación de
dos factores para el admin, sesiones multi-cuenta en el navegador y la pila de middleware que
protege todo el sitio (exigencia de login, puerta de formación inicial, seguimiento de actividad,
zona horaria).

Relación con las apps núcleo:

- **`user_levels`** — lee el nivel del usuario a través de `UserLevelProfile`. La mayoría de
  propiedades relacionadas con el nivel en `User` (`level_code`, `is_leader()`, `has_subscription`,
  `was_downgraded`) son accessors delgados que delegan en `user_levels`; las reglas en sí nunca se
  implementan aquí.
- **`core`** — helpers de notificación y constantes compartidas.
- **`communication`** — bidireccional: `User.contact` es un OneToOne a `communication.Contact`,
  mientras que `Contact.user` apunta de vuelta a `User`. Un usuario registrado desde un contacto
  mantiene ambos registros sincronizados mediante `User.save()`.

## Modelos y datos

### `User`

Extiende `AbstractBaseUser` + `PermissionsMixin`. `USERNAME_FIELD = "username"`.

| Campo | Tipo | Notas |
|---|---|---|
| `sponsor` | FK → `self` (`SET_NULL`) | Árbol de patrocinio; recorrido por `user_levels` |
| `contact` | OneToOne → `communication.Contact` (`SET_NULL`) | Contacto de origen cuando se registra desde el CRM |
| `username` | Char, unique | Identificador de login |
| `email` | Email, unique | También usado para verificación y restablecimiento de contraseña |
| `number_farmasi_influencer` | Char | Identificador de negocio obligatorio |
| `token` | Char, nullable | Token de invitación, generado por `generate_token()` |
| `name`, `phone`, `country`, `date_of_birth`, `profile_image`, `calendar_link` | — | Perfil |
| `email_status`, `email_code` | — | Estado de verificación de email |
| `initial_training_done` | bool | Consumido por `InitialTrainingGateMiddleware` |
| `is_active`, `is_staff`, `is_admin` | bool | Flags técnicos |
| `registered_at`, `last_activity` | datetime | Registro y seguimiento de actividad |
| `from_contact` | bool | Origen del registro |
| `stripe_customer_id` | Char, nullable | Asignado por `pricing` |
| `allow_unpaid_subscription` | bool | Cuentas de cortesía exentas de comprobaciones de cobro |

`UserManager.create_user` genera un `username` temporal cuando no se indica ninguno, más
`email_code` y el token de invitación. `create_superuser` exige además `is_staff` e `is_admin`.

`save()` reprocesa `profile_image` (WebP, vía `core.utils.files`) y propaga los cambios de perfil al
`Contact` vinculado.

Propiedades y métodos destacados — varios resuelven datos de otras apps mediante **importaciones
diferidas** para evitar dependencias circulares: `level_code`, `level_name`, `initial_level_name`,
`was_downgraded`, `was_leader_when_downgraded`, `has_subscription`, `has_free_trial`,
`get_end_trial_time()`, `show_subscription_correction_banner` (`user_levels`, `pricing`);
`initial_training_completed()`, `get_training_stats_data()`, `answered_input_training_fields`
(`training`); `get_daily_progress()`, `get_all_challenges_daily_progress()` (`challenge`);
`get_users_invited()` (hijos directos en el árbol de patrocinio); `is_leader()`, `is_leader_pro()`,
`is_any_leader()`, `registered_since`, `generate_token()`.

### `BrowserAccountRegistry`

FK → `User`. Una fila por cuenta registrada en un navegador, habilitando el conmutador multi-cuenta.

### `VerificationCode`

FK → `User`. Códigos de corta duración para la autenticación de dos factores del admin.

## Vistas e integración frontend

**Esta app no usa HTMX.** Cada vista devuelve una página HTML completa o una redirección; no hay
endpoints JSON ni fragmentos parciales.

Las rutas se montan en la raíz del proyecto (`Platform/urls.py` incluye `apps.users.urls` bajo
`""`), por eso poseen paths de primer nivel como `/login/`.

| Vista | URL | Propósito |
|---|---|---|
| `sing_in` | `login/` | Login |
| `register` | `<username>/register/<token>/` | Registro con token de invitación |
| `register_sponsor_link` | `<username>/register/` | Registro público mediante enlace de patrocinador |
| `email_validation` | `email-validation/` | Pantalla de verificación pendiente |
| `email_confirmation` | `email-confirmation/<user_id>/<code>/` | Confirma la dirección |
| `log_out` | `logout/` | Logout, consciente de multi-cuenta |
| `send_verification_code` / `verify_code` | `send-verification-code/`, `verify-code/` | 2FA del admin |
| `personal_link_mate` | `<username>_link/` | **Página pública Link Mate**; renderiza datos propiedad de `links` |
| `add_account`, `switch_account`, `remove_account_view`, `logout_all_accounts` | `accounts/…` | Gestión de sesión multi-cuenta |

El restablecimiento de contraseña usa `django.contrib.auth.views` con plantillas del proyecto
(`forgot-password.html`, `reset-password/…`) y formularios personalizados
`PasswordResetCustomForm` / `SetPasswordCustomForm`.

### Middleware

Todos están registrados en `settings.MIDDLEWARE`, en este orden.

| Clase | Propósito |
|---|---|
| `TimezoneFromSessionMiddleware` | Activa la zona horaria guardada en `session["django_timezone"]` |
| `AccountRegistryMiddleware` | Mantiene la sesión activa registrada en la cookie `account_registry` |
| `TwoFactorAuthMiddleware` | 2FA por email para `/admin/`; **omitido cuando `DEBUG` está activo** |
| `LoginRequiredMiddleware` | Exige autenticación en los prefijos de app; excepciones declaradas en `public_routes.py` |
| `InitialTrainingGateMiddleware` | Redirige a `/training/onboarding/` hasta que `initial_training_done` |
| `UpdateLastActivityMiddleware` | Actualiza `last_activity` como máximo una vez cada 24 h |

## Configuración y dependencias

| Setting | Propósito |
|---|---|
| `AUTH_USER_MODEL = "users.User"` | Referenciado por todas las apps del proyecto |
| `RECAPTCHA_PUBLIC_KEY`, `RECAPTCHA_PRIVATE_KEY` | `django-recaptcha` en formularios de registro y login |
| `EMAIL_HOST_PASSWORD` y ajustes SMTP | Email de verificación, invitación y restablecimiento (backend de consola cuando `DEBUG`) |
| `DEBUG` | Desactiva el 2FA del admin en desarrollo |

**No hay entrada en `AUTHENTICATION_BACKENDS`**, así que aplica el `ModelBackend` por defecto de
Django. El servicio multi-cuenta almacena `BACKEND_SESSION_KEY` de forma explícita al cambiar de
cuenta. La API móvil se autentica por separado con su propio esquema de tokens (véase
[`apps/keyboard_api/README.es.md`](../keyboard_api/README.es.md)).

Módulos de soporte:

| Módulo | Responsabilidad |
|---|---|
| `services/multi_account.py` | Registro de cuentas a nivel de navegador, cambio y eliminación |
| `utils.py` | Envío de email vía Celery, decorador `redirect_authenticated_user`, constructores de URL de registro |
| `public_routes.py` | Lista de regex de rutas exentas de `LoginRequiredMiddleware` |
| `context_processor.py` | Inyecta `saved_accounts` en cada plantilla |
| `tasks.py` | `send_email_task` (Celery) |

Dependencias de apps: `communication`, `core`, `main`, `user_levels`, e importaciones diferidas de
`training`, `challenge`, `pricing`, `links`. Externas: Celery (email), Redis (indirecto, a través de
`core`). Esta app **no tiene integración directa con Sentry ni Cloudflare**; las imágenes de perfil
pasan por `core.utils.files` y por tanto aterrizan en el backend de almacenamiento configurado de
forma global.

> **Esta app no define signals.** Existió un `signals.py` pero nunca se importó — `apps.py` no tiene
> hook `ready()` — así que sus tres receptores nunca se ejecutaron, y los tres eran redundantes:
> `Task` ya hace cascade desde `Challenge` e `Incentive` vía `on_delete=CASCADE`, y las cachés de
> `main` que intentaba limpiar se invalidan donde corresponde por `training.signals` y
> `training.views`. La invalidación de nivel, sponsor y perfil para `User` vive en
> `user_levels/signals.py`.
