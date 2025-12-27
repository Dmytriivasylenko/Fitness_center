import os
import smtplib
import ssl

from celery import Celery

#app = Celery('task', broker='pyamqp:guest://guest@localhost:5672//')
app = Celery('task', broker='amqp://guest:guest@localhost:5672//')




@app.task
def add(x, y):
    print(x + y)
    return x + y

@app.task
def send_mail(recipient, subject, text):
    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = "vasylenkodmytrii@gmail.com"
    receiver_email = recipient
    password = os.environ.get("EMAIL_PASSWORD")
    message = text

    context = ssl.create_default_context()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    with smtplib.SMTP(host=smtp_server, port=port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

