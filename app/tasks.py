import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from celery import Celery

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SENDER_EMAIL  = os.environ.get("EMAIL_SENDER", "vasylenkodmytrii@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

app = Celery("tasks", broker="amqp://guest:guest@localhost:5672//")


#helpers

def _build_message(recipient: str, subject: str, body: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = recipient
    msg.attach(MIMEText(body, "plain", "utf-8"))
    return msg


def _send(recipient: str, subject: str, body: str) -> None:
    msg = _build_message(recipient, subject, body)
    context = ssl.create_default_context()

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient, msg.as_string())


# tasks

@app.task
def add(x, y):
    result = x + y
    print(result)
    return result


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_mail(self, recipient: str, subject: str, body: str) -> None:
    try:
        _send(recipient, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, recipient: str, login: str, login_url: str) -> None:
    subject = "Welcome to FitnessHub 💪"
    body = (
        f"Hi {login},\n\n"
        f"Your account is ready. Start your fitness journey here:\n{login_url}\n\n"
        f"Stay consistent,\nFitnessHub Team"
    )
    try:
        _send(recipient, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_admin_new_user_email(self, login: str, email: str, phone: str) -> None:
    admin_email = os.environ.get("ADMIN_EMAIL", SENDER_EMAIL)
    subject = f"New registration: {login}"
    body = (
        f"New user registered:\n\n"
        f"Login: {login}\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n"
    )
    try:
        _send(admin_email, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task
def test_task() -> str:
    print("✅ Celery is working!")
    return "ok"