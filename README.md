# AI-MSHM Backend

**AI-Driven Multi-Source Health Measurement System** — Django REST API

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5 + Django REST Framework |
| Database | MongoDB via Djongo |
| Auth | JWT (SimpleJWT) with token blacklisting |
| Real-time | Django Channels 4 + Redis channel layer |
| Task Queue | Celery + Redis broker |
| File Storage | Cloudinary |
| ASGI Server | Daphne |
| API Docs | drf-spectacular (Swagger + ReDoc) |

---

## Project Structure

```
ai_mshm_backend/
│
├── config/                     # Django project config
│   ├── settings/
│   │   ├── base.py             # Shared settings
│   │   ├── development.py      # Dev overrides
│   │   └── production.py       # Production overrides
│   ├── urls.py                 # Root URL router
│   ├── asgi.py                 # HTTP + WebSocket routing
│   └── celery.py               # Celery app
│
├── apps/
│   ├── accounts/               # Auth: register, login, email verify, password reset
│   │   ├── models.py           # User, EmailVerificationToken, PasswordResetToken
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py         # Business logic (thin views, fat services)
│   │   ├── tasks.py            # Celery: send emails async
│   │   └── urls.py
│   │
│   ├── onboarding/             # 6-step onboarding flow
│   │   ├── models.py           # OnboardingProfile (steps 1–6)
│   │   ├── serializers.py      # Per-step serializers
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── notifications/          # In-app notifications + WebSocket
│   │   ├── models.py           # Notification
│   │   ├── consumers.py        # WebSocket consumer
│   │   ├── services.py         # NotificationService.send()
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── routing.py          # WebSocket URL patterns
│   │   └── urls.py
│   │
│   └── settings_app/           # User settings
│       ├── models.py           # NotificationPreferences, ConnectedDevice, PrivacySettings
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
│
├── core/                       # Shared utilities (no business logic)
│   ├── middleware.py           # Request logging + JWT WebSocket auth
│   ├── responses.py            # Standardised API response helpers
│   ├── pagination.py           # StandardResultsPagination
│   ├── exceptions/
│   │   └── handlers.py         # Custom DRF exception handler
│   └── utils/
│       └── helpers.py          # Token gen, hashing, time utils
│
├── docs/
│   └── rest/                   # .rest files for VS Code REST Client
│       ├── auth.rest
│       ├── onboarding.rest
│       ├── notifications.rest
│       └── settings.rest
│
├── templates/
│   └── emails/
│       ├── verify_email.html
│       └── reset_password.html
│
├── .env.example                # Copy to .env and fill in values
├── docker-compose.yml          # Full local stack
├── Dockerfile
├── manage.py
└── requirements.txt
```

---

## Quick Start

### 1. Clone & environment

```bash
git clone <repo-url>
cd ai_mshm_backend
cp .env.example .env
# Edit .env with your values
```

### 2. Option A — Docker (recommended)

```bash
docker compose up -d
docker compose exec api python manage.py migrate
docker compose exec api python manage.py createsuperuser
```

### 3. Option B — Local virtualenv

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start MongoDB and Redis locally (or use Docker just for them)
docker compose up -d mongodb redis

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# In a second terminal — Celery worker
celery -A config worker -l info

# In a third terminal — Celery beat (optional)
celery -A config beat -l info
```

---

## API Reference

| URL | Description |
|---|---|
| `GET /api/docs/` | Swagger UI (interactive) |
| `GET /api/redoc/` | ReDoc |
| `GET /api/schema/` | Raw OpenAPI 3 JSON |

---

## API Endpoints Summary

### Auth — `/api/v1/auth/`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `register/` | ❌ | Register patient or clinician |
| POST | `login/` | ❌ | Login → JWT token pair |
| POST | `token/refresh/` | ❌ | Refresh access token |
| POST | `logout/` | ✅ | Blacklist refresh token |
| POST | `verify-email/` | ❌ | Verify email with token |
| POST | `resend-verification/` | ❌ | Resend verification email |
| POST | `forgot-password/` | ❌ | Request password reset |
| POST | `reset-password/` | ❌ | Reset with token |
| GET  | `me/` | ✅ | Get current user |
| PATCH | `me/` | ✅ | Update name/avatar |
| POST | `me/change-password/` | ✅ | Change password |

### Onboarding — `/api/v1/onboarding/`

| Method | Path | Description |
|---|---|---|
| GET   | `profile/` | Full onboarding profile |
| PATCH | `step/1/` | Personal info |
| PATCH | `step/2/` | Physical measurements (BMI auto-computed) |
| PATCH | `step/3/` | Skin changes |
| PATCH | `step/4/` | Menstrual history |
| PATCH | `step/5/` | Wearable setup |
| POST  | `step/6/rppg/` | Mark rPPG baseline captured |
| POST  | `complete/` | Mark onboarding complete |

### Notifications — `/api/v1/notifications/`

| Method | Path | Description |
|---|---|---|
| GET   | `/` | List notifications (paginated) |
| GET   | `/unread-count/` | Unread badge count |
| PATCH | `/mark-all-read/` | Mark all as read |
| PATCH | `/<id>/read/` | Mark one as read |
| DELETE | `/<id>/` | Delete notification |

**WebSocket:** `ws://host/ws/notifications/?token=<access_token>`

### Settings — `/api/v1/settings/`

| Method | Path | Description |
|---|---|---|
| GET/PATCH | `notifications/` | Notification preferences |
| GET/POST  | `devices/` | List / connect wearable |
| GET/PATCH/DELETE | `devices/<id>/` | Manage single device |
| POST | `devices/<id>/sync/` | Trigger manual sync |
| GET/PATCH | `privacy/` | Privacy & consent settings |
| POST | `privacy/export/` | Request data export |
| DELETE | `privacy/delete-account/` | Permanently delete account |

---

## Testing .rest files

Install **REST Client** extension in VS Code (Huachao Mao), then open any file in `docs/rest/` and click **Send Request** above each block.

JetBrains IDEs support `.http` / `.rest` files natively.

---

## Standard Response Envelope

All endpoints return:

```json
{
  "status": "success",
  "message": "Request successful",
  "data": { ... },
  "meta": { "count": 100, "next": "...", "previous": null }
}
```

Errors:

```json
{
  "status": "error",
  "message": "Validation failed.",
  "data": null,
  "errors": { "email": ["Enter a valid email address."] }
}
```

---

## WebSocket — Real-time Notifications

Connect with JWT token:
```
ws://localhost:8000/ws/notifications/?token=<access_token>
```

**Client → Server actions:**
```json
{ "action": "mark_read",    "notification_id": 42 }
{ "action": "mark_all_read" }
```

**Server → Client events:**
```json
{ "type": "new_notification", "notification": { ... } }
{ "type": "unread_count",     "count": 5 }
{ "type": "marked_read",      "notification_id": 42 }
{ "type": "all_marked_read",  "count": 5 }
```

---

## Adding New Notifications (from code)

```python
from apps.notifications.services import NotificationService
from apps.notifications.models import Notification

NotificationService.send(
    recipient=user,
    notification_type=Notification.NotificationType.RISK_UPDATE,
    title="Risk score updated",
    body="Your PCOS risk score has changed to Medium.",
    priority=Notification.Priority.HIGH,
    data={"risk_score": 62, "previous": 45},
)
```

This persists the record to MongoDB **and** pushes it to the user's open WebSocket connection in one call.

