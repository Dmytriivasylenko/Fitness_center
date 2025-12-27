import json
import os
import stripe
from datetime import datetime, timedelta

from flask import Flask, render_template, redirect
from flask_login import LoginManager, current_user
from werkzeug.utils import secure_filename

from app.database import init_db
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



# ==================== FLASK APP ====================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "../templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.config["SECRET_KEY"] = "_343435#y2L_F4Q8z_super_static_key"
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# ==================== LOGIN MANAGER ====================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    user = db_session.get(User, int(user_id))
    if not user:
        print("⚠️ user_loader: user not found:", user_id)
    return user


# ==================== BLUEPRINTS ====================
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(services_bp)
app.register_blueprint(trainers_bp)
app.register_blueprint(reservations_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(admin_bp)

# ==================== GLOBALS ====================
app.jinja_env.globals["now"] = datetime.now

# ==================== DB INIT ====================
init_db()

# ==================== HOME (LANDING) ====================
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect("/user")
    return render_template("index.html")

# ==================== CELERY TEST ====================
@app.route("/test_celery")
def celery_test():
    test_task.delay()
    return "Celery task sent!"

# ==================== UPLOADS ====================
UPLOAD_FOLDER = "app/static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER




from app.database import db_session

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


# ==================== RUN APP ====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
