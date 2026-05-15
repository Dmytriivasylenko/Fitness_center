from app.celery_app import celery
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import ssl


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "vasylenkodmytrii@gmail.com"
PASSWORD = os.environ.get("EMAIL_PASSWORD")


def send_email(recipient: str, subject: str, html_body: str):
    """
    Core function for sending emails, used by Celery tasks.
    Works through Gmail SMTP with TLS.
    """
    if not PASSWORD:
        print("❌ EMAIL_PASSWORD is missing – email will NOT be sent")
        return

    if not recipient:
        print("❌ Recipient email is empty – email will NOT be sent")
        return

    print(f"[EMAIL] Preparing to send email to: {recipient} | subject: {subject}")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    ctx = ssl.create_default_context()

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=ctx)
            server.login(SENDER_EMAIL, PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error while sending email to {recipient}: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error while sending email to {recipient}: {e}")
        raise
    else:
        print(f"📧 Email successfully sent to {recipient}")


# ====================== CELERY TASKS ==========================

@celery.task
def test_task():
    print("Celery OK!")
    return "OK"


@celery.task
def send_welcome_email_task(recipient: str, username: str, login_url: str):
    print(f"[TASK] send_welcome_email_task → {recipient}")
    html = f"""
    <h2>Welcome, {username}!</h2>
    <p>Your registration is successful.</p>
    <p>You can log in here: <a href="{login_url}">Login</a></p>
    """
    send_email(recipient, "Welcome to FitnessApp!", html)


@celery.task
def send_admin_new_user_email_task(login: str, email: str, phone: str):
    print(f"[TASK] send_admin_new_user_email_task → admin notification for {login}")
    html = f"""
    <h2>New User Registered</h2>
    <p>Login: {login}</p>
    <p>Email: {email}</p>
    <p>Phone: {phone}</p>
    """
    send_email("vasylenkodmytrii@gmail.com", "New Registration Alert", html)


@celery.task
def send_booking_confirmation_email_task(recipient, username, service_name, trainer_name, date, time):
    print(f"[TASK] send_booking_confirmation_email_task → {recipient}")
    html = f"""
    <h2>Your Booking Is Confirmed!</h2>
    <p>Hello {username},</p>
    <p>You booked: <b>{service_name}</b></p>
    <p>Trainer: <b>{trainer_name}</b></p>
    <p>Date: {date}, Time: {time}</p>
    """
    send_email(recipient, "Booking Confirmation", html)


@celery.task
def send_booking_updated_email_task(recipient, username, date, time):
    print(f"[TASK] send_booking_updated_email_task → {recipient}")
    html = f"""
    <h2>Your Booking Was Updated</h2>
    <p>Hello {username},</p>
    <p>New date: <b>{date}</b></p>
    <p>New time: <b>{time}</b></p>
    """
    send_email(recipient, "Booking Updated", html)


@celery.task
def send_booking_canceled_email_task(recipient, username):
    print(f"[TASK] send_booking_canceled_email_task → {recipient}")
    html = f"""
    <h2>Your Booking Was Canceled</h2>
    <p>Hello {username},</p>
    <p>Your reservation is canceled.</p>
    """
    send_email(recipient, "Booking Canceled", html)


# ========= PUBLIC FUNCTIONS (alias for app/utils) ==================

def send_welcome_email(recipient, username, login_url):
    print(f"[PUBLIC] send_welcome_email → queue task for {recipient}")
    send_welcome_email_task.delay(recipient, username, login_url)


def send_admin_new_user_email(login, email, phone):
    print(f"[PUBLIC] send_admin_new_user_email → queue task for {login}")
    send_admin_new_user_email_task.delay(login, email, phone)


def send_booking_confirmation_email(recipient, username, service_name, trainer_name, date, time):
    print(f"[PUBLIC] send_booking_confirmation_email → queue task for {recipient}")
    send_booking_confirmation_email_task.delay(recipient, username, service_name, trainer_name, date, time)


def send_booking_updated_email(recipient, username, date, time):
    print(f"[PUBLIC] send_booking_updated_email → queue task for {recipient}")
    send_booking_updated_email_task.delay(recipient, username, date, time)


def send_booking_canceled_email(recipient, username):
    print(f"[PUBLIC] send_booking_canceled_email → queue task for {recipient}")
    send_booking_canceled_email_task.delay(recipient, username)
