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
- **`core`** — `BaseForm`, helpers de respuesta HTMX (`attach_toast_trigger`, `htmx_error_response`),
  el endpoint genérico de reordenación `update_drag_drop` y helpers de registro en admin.

## Modelos y datos

| Modelo | Relaciones |
|---|---|
| `LinkMate` | OneToOne → `users.User`. Contenedor raíz: nombre visible, bio, avatar, enlace de tienda |
| `LinkMateCustomization` | OneToOne → `LinkMate`; FK → `PredefinedBackground` — tipografía, colores, fondo |
| `LinkMateProCustomization` | OneToOne → `LinkMate` — layout PRO, incluido `get_embed_video_url()` para YouTube |
| `PersonalLink` | FK → `LinkMate` — enlaces ordenados; `is_pro` separa la lista estándar de la PRO |
| `SocialMedia` | Catálogo de redes soportadas; sin FK a usuario |
| `SocialMediaLinkMate` | FK → `LinkMate`; FK → `SocialMedia` — redes sociales del usuario |

El botón de contacto no tiene fila propia: comparte la escala de orden de los enlaces personales y su
posición se guarda en `LinkMate.order_contact_me`.

## Módulos

| Módulo | Responsabilidad |
|---|---|
| `services.py` | Persistencia: toggles, guardado de enlaces/redes/personalización PRO, borrados y reordenación de la lista personal |
| `utils.py` | Constructores de contexto (`build_link_mate_context`, `build_ordered_items`) y renderizado de parciales HTMX |
| `const.py` | Claves de tipo de elemento y el nombre del evento cliente `linkMatePreviewRefresh` |
| `forms.py` | Formularios de modelo; `LinkMateCustomizationForm` valida un solo campo de apariencia por petición |

Todas las mutaciones se acotan al `LinkMate` de `request.user`; ninguna vista confía en un id que
llegue del cliente por sí solo.

## Vistas e integración frontend

**Esta app usa HTMX** en todas sus mutaciones. Formularios y controles envían con `hx-post`; las
vistas responden con el parcial de la lista afectada (o `204`) más un `HX-Trigger` que lleva el toast
de éxito y `linkMatePreviewRefresh`. Los errores de validación vuelven como `422` desde
`htmx_error_response`, que el handler global de `core.js` convierte en toast de error dejando el
modal abierto.

Prefijo de URL: **`/links/`**. La página pública está fuera de esta app, en `<username>_link/`
(`users.views.personal_link_mate`).

| URL | Vista | Comportamiento HTMX |
|---|---|---|
| `link-mate` | `link_mate` | Panel de edición (solo GET) |
| `toggle-item/` | `toggle_link_item` | Interruptores de visibilidad → `204` |
| `load-personal-link-form/` | `load_personal_link_form` | Parcial GET → `partials/personal-link-fields.html` (`?pro=1` para la lista PRO) |
| `save-personal-link/` | `save_personal_link` | Devuelve `personal-links.html` o `pro-links.html` |
| `load-social-link-form/` | `load_social_link_form` | Parcial GET → `partials/social-link-fields.html` |
| `save-social-link/` | `save_social_link` | Devuelve `social-links.html` |
| `delete-link/` | `delete_link` | Devuelve la lista afectada y fija `HX-Retarget` |
| `save-store-link/` | `save_store_link` | Devuelve `personal-links.html` |
| `save-link-mate/` | `save_link_mate` | Autoguardado silencioso al blur → `204` |
| `save-link-mate-pro/` | `save_link_mate_pro` | Personalización PRO → `204` |
| `save-customization/` | `save_link_mate_customization` | Re-renderiza el grupo de control (fuente, forma, fondo) o `204` |
| `reorder-items/` | `reorder_items` | Orden de la lista personal incluyendo el botón de contacto → `204` |

Las listas del editor —enlaces personales, redes sociales y PRO— comparten
`components/partials/link-list-row.html` para la estructura de cada fila (agarre, título que salta
de línea, borrar e interruptor). Quien incluye el parcial pasa el texto visible como `title`
(`item.label` en las filas mixtas de la lista personal; `.name` en PRO y redes sociales).

Modales: `modal-link.html` (personal y PRO) lo gobierna el cargador global `htmx_modal_form.js`;
`modal-social-link.html` y `modal-store-link.html` usan `hx-get` / `hx-post` en línea. El
`modal-delete-confirm.html` compartido pasa a HTMX cuando se incluye con `delete_hx=1`.

### JavaScript

`static/js/link-mate.js` es el único script propio de la app. Contiene lo que HTMX no puede expresar
de forma declarativa: el custom element `<link-preview-frame>` (iframe diferido, recarga con debounce
ante `linkMatePreviewRefresh`), la persistencia de pestaña, el binding de SortableJS de la lista
personal, la vista previa de color en vivo y el relleno de los modales de borrado y de tienda.

La reordenación de las listas PRO y social usa el sistema global de drag & drop
(`static/js/sortable-list.js` → `update_drag_drop`), declarado solo con atributos `data-*`. La lista
personal conserva su endpoint propio porque el botón de contacto participa en el orden sin ser una
fila de base de datos, algo que el endpoint genérico no puede expresar: actualiza un campo de un
modelo. Su orden se envía con `htmx.ajax`, así que ninguna petición de esta app lee la cookie CSRF.

## Configuración y dependencias

| Setting | Propósito |
|---|---|
| `R2_*` / `STORAGES` | Avatares e imágenes de fondo a través del backend de media global |
| `FORMS_URLFIELD_ASSUME_HTTPS` | Permite escribir la URL de tienda sin esquema |
| `RESTRICTED_ALERT_LINK_APPEARANCE` (desde `user_levels.const`) | Textos del modal de upgrade de apariencia |

La única integración externa es el embed de YouTube en `LinkMateProCustomization`. **No usa
Sentry, Redis, Celery ni Stripe.**

Dependencias de la app: `core`, `user_levels` (solo la constante) y `users` para la ruta pública.
