# links

## Descripción

«Link Mate»: una página link-in-bio por usuario. Cada usuario tiene un `LinkMate` con enlaces
personales, redes sociales, un enlace de tienda opcional y personalización visual. Los usuarios PRO
desbloquean un layout ampliado con su propio conjunto de enlaces y un vídeo embebido.

Relación con las apps núcleo:

- **`users.User`** — OneToOne con `LinkMate`; la página pública la sirve `users.views.personal_link_mate`
  en `<username>_link/`, no esta app.
- **`user_levels`** — esta app es la excepción al patrón habitual: **no** llama a
  `check_action_allowed` ni a ningún helper de visibilidad. Solo importa `RESTRICTED_ALERT_LINK_APPEARANCE`
  desde `user_levels.const` para mostrar el modal de upgrade en la plantilla. El gating de nivel del
  layout PRO es presentacional.
- **`core`** — `BaseForm` y helpers de registro en admin.

## Modelos y datos

| Modelo | Relaciones |
|---|---|
| `LinkMate` | OneToOne → `users.User`. Contenedor raíz: nombre visible, bio, avatar, enlace de tienda |
| `LinkMateCustomization` | OneToOne → `LinkMate`; FK → `PredefinedBackground` — tipografía, colores, fondo |
| `LinkMateProCustomization` | OneToOne → `LinkMate` — layout PRO, incluido `get_embed_video_url()` para YouTube |
| `PersonalLink` | FK → `LinkMate` — enlaces personalizados ordenados |
| `SocialMedia` | Catálogo de redes soportadas; sin FK a usuario |
| `SocialMediaLinkMate` | FK → `LinkMate`; FK → `SocialMedia` — redes sociales del usuario |

No hay `services.py` ni `utils.py`; la lógica vive en `views.py`, `forms.py` y el JS estático.
El orden se persiste mediante endpoints de reordenación dedicados.

## Vistas e integración frontend

**Esta app no usa HTMX.** La edición combina posts de formulario estándar con redirección y
endpoints AJAX que devuelven `JsonResponse`; ninguna vista devuelve un fragmento HTML.

Prefijo de URL: **`/links/`**. La página pública está fuera de esta app, en `<username>_link/`
(`users.views.personal_link_mate`).

| URL | Vista | Respuesta |
|---|---|---|
| `link-mate` | `link_mate` | Panel de edición (HTML); los toggles de visibilidad responden JSON |
| `save-link/<link_mate_id>` · `save-pro-link/<link_mate_id>` | `save_link`, `save_pro_link` | CRUD de enlaces personales (redirect) |
| `save-link-mate-pro/` | `save_link_mate_pro` | Personalización PRO (redirect) |
| `save-social-media-link/` | `save_social_media_link` | CRUD de enlaces sociales (redirect) |
| `delete-link/` | `delete_link` | Elimina un enlace personal o social (redirect) |
| `save-store-link/` | `save_store_link` | URL de tienda (redirect) |
| `save-link-mate/` | `save_link_mate` | Datos básicos de Link Mate (JSON) |
| `save-customization/` | `save_link_mate_customization` | Tipografía, color, fondo (JSON) |
| `reorder-items/` · `reorder-pro-items/` · `reorder-social-media-items/` | `reorder_items`, `reorder_pro_items`, `reorder_social_media_items` | Orden por drag-and-drop (JSON) |

## Configuración y dependencias

| Setting | Propósito |
|---|---|
| `R2_*` / `STORAGES` | Avatares e imágenes de fondo a través del backend de media global |
| `LIMIT_USER_LINKS` (desde `core.const`) | Tope de enlaces personales por usuario |
| `RESTRICTED_ALERT_LINK_APPEARANCE` (desde `user_levels.const`) | Textos del modal de upgrade de apariencia |

La única integración externa es el embed de YouTube en `LinkMateProCustomization`. **No usa
Sentry, Redis, Celery ni Stripe.**

Dependencias de la app: `core`, `user_levels` (solo la constante) y `users` para la ruta pública.
