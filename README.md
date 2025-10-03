# Librioo — Plataforma para escritores y lectores (Django 5)

Este proyecto implementa las funcionalidades solicitadas para **escritores** y **lectores** sobre tus plantillas estáticas.
Incluye gestión de libros y capítulos, comentarios, likes, encuestas, comunidad, clubs, notificaciones, seguimiento y ventas con Stripe.

## Instalación rápida

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations accounts library community payments notifications
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Variables de entorno (opcional, para pagos y email)

- `STRIPE_SECRET_KEY` — clave secreta de Stripe
- `STRIPE_PRICE_BOOK_<BOOK_ID>` — (opcional) price id para cada libro de pago
- `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, `EMAIL_USE_TLS`

## Publicación programada de capítulos
Hay un comando para publicar capítulos programados. Ejecútalo por cron cada 5 minutos:
```bash
python manage.py publish_scheduled_chapters
```

## Estructura de apps
- `apps/accounts` — Usuario, perfiles, social login (allauth)
- `apps/library` — Libros, capítulos, categorías, colaboraciones, comentarios, likes, encuestas, métricas
- `apps/community` — Muro, retos, clubs y membresías
- `apps/notifications` — Notificaciones y suscripciones (seguir libros/usuarios)
- `apps/payments` — Compra de libros vía Stripe
- `apps/common` — Reportes/moderación, utilidades

Los HTML/CSS/JS de tu plantilla están integrados en `apps/library/templates` y `apps/library/static`.
