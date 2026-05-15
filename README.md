# Fitness Center Management Platform

A production-ready web application for managing fitness center operations — bookings, trainers, services, payments, and admin workflows.

Built with Flask, PostgreSQL, Celery, RabbitMQ, Docker, and Gunicorn.

---

## Features

### Users
- Register and log in with validated credentials
- Edit profile and upload avatar
- Change password securely
- Top up balance via Stripe Checkout
- Book services with specific trainers
- Real-time slot conflict detection — no double bookings
- View transaction history
- Email notifications for bookings, updates, and cancellations

### Admin Panel
- Manage users, trainers, and services
- Soft delete — deactivate instead of hard delete
- Manage reservations: reschedule, cancel, restore
- Calendar view
- Export reports to Excel
- Audit log — tracks who changed what and when

### Payments
- Stripe Checkout integration
- Funds deducted on booking
- Automatic refund on cancellation

---

## Tech Stack

| Area | Tools |
|------|-------|
| Backend | Flask, SQLAlchemy, Alembic |
| Auth | Flask-Login, Flask-Limiter |
| Async tasks | Celery + RabbitMQ |
| Database | PostgreSQL |
| Payments | Stripe |
| Email | Gmail SMTP |
| Config | pydantic-settings, .env |
| Deploy | Docker, Docker Compose, Gunicorn |
| Testing | pytest, pytest-mock |
| CI/CD | GitHub Actions |

---

## Security

- Rate limiting on auth endpoints: 5 login attempts per minute per IP
- All secrets managed via `.env` with pydantic-settings validation
- Secret key validated at startup — weak keys are rejected
- Soft delete preserves data integrity

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Stripe account (for payments)
- Gmail account with App Password (for emails)

### 1. Clone the repository
```bash
git clone git@github.com:Dmytriivasylenko/Fitness_center.git
cd Fitness_center
```

### 2. Create `.env` file
```env
SECRET_KEY=generate-with-python-secrets-token-hex-32
FLASK_ENV=development
DEBUG=false

POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=fitness_db
DATABASE_URL=postgresql+psycopg2://postgres:yourpassword@postgres:5432/fitness_db

CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=rpc://

STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...

EMAIL_PASSWORD=your-gmail-app-password
MAIL_USERNAME=your@gmail.com

UPLOAD_FOLDER=app/static/uploads
```

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> ⚠️ Never commit `.env` to Git. It is already in `.gitignore`.

### 3. Run with Docker
```bash
docker compose up --build
```

This starts 4 containers:
- `flask_app` — Gunicorn WSGI server on port 5000
- `postgres` — PostgreSQL 17
- `rabbitmq` — RabbitMQ message broker
- `celery_worker` — async email and task processing

App available at: http://localhost:5000

### 4. Run without Docker (local dev)

```bash
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS / Linux

pip install -r requirements.txt
pip install -r requirements-dev.txt

flask run
```

Start Celery worker separately:
```bash
celery -A app.celery_app.celery worker --loglevel=info
```

---

## Testing

```bash
pytest tests/ -v
```

25 tests covering:
- Reservation creation with conflict detection
- Soft-delete cancellation with refund
- Rescheduling logic
- Authentication and credential validation
- Registration form validation

---

## CI/CD

GitHub Actions pipeline runs automatically on every push to `master`:

1. Spins up PostgreSQL service container
2. Installs dependencies
3. Runs full pytest suite
4. Builds Docker image (only if tests pass)

---

## Project Structure

```
Fitness_center/
├── app/
│   ├── routes/          # Blueprints: auth, admin, reservations, profile...
│   ├── models.py        # SQLAlchemy models with type hints
│   ├── utils.py         # Business logic: reservations, payments
│   ├── config.py        # pydantic-settings configuration
│   ├── tasks.py         # Celery async tasks
│   └── database.py      # DB session setup
├── tests/
│   ├── conftest.py      # pytest fixtures
│   └── test_utils.py    # 25 unit tests
├── alembic/             # DB migrations
├── templates/           # Jinja2 HTML templates
├── .github/workflows/   # GitHub Actions CI/CD
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Health Check

```
GET /health
→ {"status": "ok", "env": "production"}
```

---

## Payments Testing

Use Stripe test card: `4242 4242 4242 4242`, any future date, any CVC.
