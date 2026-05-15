import os
import stripe
from datetime import datetime

from flask import Flask, render_template, redirect, jsonify
from flask_login import LoginManager, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import settings
from app.database import init_db, db_session
from app import database
from app.models import User
from app.routes import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.services import services_bp
from app.routes.trainers import trainers_bp
from app.routes.reservations import reservations_bp
from app.routes.profile import profile_bp
from app.routes.admin import admin_bp
from app.tasks import test_task


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "../templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)


app.config["SECRET_KEY"] = settings.secret_key
app.config["UPLOAD_FOLDER"] = settings.upload_folder

stripe.api_key = settings.stripe_secret_key

#Limiter
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],        # no global limit — only per-route
    storage_uri="memory://",  # swap to "redis://redis:6379" in production
)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id: str):
    user = db_session.get(User, int(user_id))
    if not user:
        print("⚠️ user_loader: user not found:", user_id)
    return user

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(services_bp)
app.register_blueprint(trainers_bp)
app.register_blueprint(reservations_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(admin_bp)


app.jinja_env.globals["now"] = datetime.now

#Db
init_db()
os.makedirs(settings.upload_folder, exist_ok=True)

#rate limit
@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify(
        error="Too many requests",
        message="Too many attempts. Please try again in a minute.",
        retry_after=60,
    ), 429

#home
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect("/user")
    return render_template("index.html")

#celery test
@app.route("/test_celery")
def celery_test():
    test_task.delay()
    return "Celery task sent!"

#health check
@app.route("/health")
def health():
    return {"status": "ok", "env": settings.flask_env}, 200


@app.teardown_appcontext
def shutdown_session(exception=None):
    if hasattr(db_session, "remove"):
        db_session.remove()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=settings.debug)
