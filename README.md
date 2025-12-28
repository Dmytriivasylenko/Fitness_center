# 🏋️ FitnessApp

> A simple training booking platform I built while learning Flask.

Users can register, book trainings, manage their balance, and receive notifications.  
Admins get a dashboard to manage trainers, services, users, and reservations.



## ✨ Features

### 👤 Users
- Register & log in  
- Edit profile + upload avatar  
- Change password  
- Top up balance  
- Book services and trainers  
- View transactions history  
- Email notifications

### 🛠 Admin Panel
- Manage users, trainers and services  
- Soft delete (deactivate instead of removing)  
- Manage reservations (reschedule, cancel, restore)  
- Calendar view  
- Export to Excel  
- Audit log (who changed what)

### 💳 Payments
- Stripe Checkout  
- Charge on booking  
- Refund on cancellation  

---

## 🧰 Tech Stack

| Area | Tools |
|------|-------|
| Backend | Flask, SQLAlchemy |
| Auth | Flask-Login |
| Async tasks | Celery + Redis |
| DB | PostgreSQL / SQLite |
| Payments | Stripe |
| Email | Gmail SMTP |
| Deploy | Docker (optional) |

---

## 🚀 Getting Started

### 1️⃣ Clone & create virtual environment
```bash
git clone <your-repo-url>
cd fitnessapp
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
2️⃣ Install dependencies
bash
Copy code
pip install -r requirements.txt
3️⃣ Create .env
env
Copy code
DATABASE_URL=postgresql://user:password@localhost:5432/fitnessapp
SECRET_KEY=some-secret
EMAIL_PASSWORD=your-gmail-app-password
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
REDIS_URL=redis://localhost:6379/0
⚠️ Do not commit this file.

4️⃣ Initialize database
bash
Copy code
python
>>> from app.database import init_db
>>> init_db()
(Optional) seed demo data:

bash
Copy code
python seed.py
5️⃣ Run the app
bash
Copy code
flask run
App will be available at:
👉 http://localhost:5000

⏱ Celery (emails & async jobs)
bash
Copy code
celery -A app.celery_app.celery worker --loglevel=info
Redis must be running.

🐳 Docker (optional)
bash
Copy code
docker compose up --build
Runs:

Flask
PostgreSQL
Redis
Celery worker

💳 Testing payments
Set Stripe keys in .env
Open Profile → Add funds
Go through checkout flow

📁 Project Structure
text
Copy code
app/
 ├─ routes/
 ├─ models/
 ├─ tasks/
 ├─ templates/
 ├─ static/
 └─ utils.py
🔭 Roadmap
Improve UI/UX

More admin analytics

Optional push notifications
