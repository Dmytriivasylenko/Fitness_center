import asyncio
from flask import Blueprint, render_template, request, redirect, abort, send_file
from datetime import datetime
from math import ceil
from openpyxl import Workbook
import io
from sqlalchemy import func
from flask_login import current_user

from app import database
from app.models import User, Trainer, Service, Reservation, AuditLog
from app.decorators import login_required, admin_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ================== STUB NOTIFIER (safe) ==================
# if we return to Telegram later — we will simply replace this
async def notify_reservation_update(reservation, action):
    # intentionally empty
    return


# ====== helper: write audit records ======
def log_action(action, entity, entity_id=None):
    entry = AuditLog(
        user_id=current_user.id,
        action=action,
        entity=entity,
        entity_id=entity_id,
    )
    database.db_session.add(entry)
    database.db_session.commit()


# ================= DASHBOARD =================
@admin_bp.route("/")
@login_required
@admin_required
def admin_dashboard():
    return render_template(
        "admin/dashboard.html",
        users_count=database.db_session.query(User).count(),
        services_count=database.db_session.query(Service).count(),
        trainers_count=database.db_session.query(Trainer).count(),
        reservations_count=database.db_session.query(Reservation).count(),
        active="admin",
    )


# ================= SERVICES (SOFT DELETE) =================
@admin_bp.route("/services")
@login_required
@admin_required
def admin_services():
    show_inactive = request.args.get("inactive") == "1"

    query = database.db_session.query(Service)
    if not show_inactive:
        query = query.filter(Service.is_active == True)

    services = query.order_by(Service.id).all()

    return render_template(
        "admin/services.html",
        services=services,
        show_inactive=show_inactive,
        active="admin",
    )


@admin_bp.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_service(service_id):
    service = database.db_session.get(Service, service_id)

    if request.method == "POST":
        if not service:
            service = Service(
                name=request.form["name"],
                price=float(request.form.get("price", 0)),
                is_active=True,
            )
            database.db_session.add(service)
            database.db_session.commit()
            log_action("create", "service", service.id)
        else:
            service.name = request.form["name"]
            service.price = float(request.form.get("price", 0))
            database.db_session.commit()
            log_action("update", "service", service.id)

        return redirect("/admin/services")

    return render_template("admin/service_form.html", service=service, active="admin")


@admin_bp.route("/services/<int:service_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_service(service_id):
    service = database.db_session.get(Service, service_id)
    if service:
        service.is_active = False
        database.db_session.commit()
        log_action("deactivate", "service", service.id)

    return redirect("/admin/services")


# ================= TRAINERS (SOFT DELETE) =================
@admin_bp.route("/trainers")
@login_required
@admin_required
def admin_trainers():
    show_inactive = request.args.get("inactive") == "1"

    query = database.db_session.query(Trainer)
    if not show_inactive:
        query = query.filter(Trainer.is_active == True)

    trainers = query.order_by(Trainer.id).all()

    return render_template(
        "admin/trainers.html",
        trainers=trainers,
        show_inactive=show_inactive,
        active="admin",
    )


@admin_bp.route("/trainers/add", methods=["GET", "POST"])
@login_required
@admin_required
def admin_add_trainer():
    if request.method == "POST":
        trainer = Trainer(
            name=request.form["name"],
            specialization=request.form["specialization"],
            gym_id=int(request.form["gym_id"]),
        )
        database.db_session.add(trainer)
        database.db_session.commit()
        log_action("create", "trainer", trainer.id)
        return redirect("/admin/trainers")

    return render_template("admin/trainer_form.html", trainer=None, active="admin")


@admin_bp.route("/trainers/<int:trainer_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_trainer(trainer_id):
    trainer = database.db_session.get(Trainer, trainer_id)
    if not trainer:
        abort(404)

    if request.method == "POST":
        trainer.name = request.form["name"]
        trainer.gym_id = int(request.form["gym_id"])
        database.db_session.commit()
        log_action("update", "trainer", trainer.id)
        return redirect("/admin/trainers")

    return render_template("admin/trainer_form.html", trainer=trainer, active="admin")


@admin_bp.route("/trainers/<int:trainer_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_trainer(trainer_id):
    trainer = database.db_session.get(Trainer, trainer_id)
    if trainer:
        trainer.is_active = False
        database.db_session.commit()
        log_action("deactivate", "trainer", trainer.id)

    return redirect("/admin/trainers")


# ================= RESERVATIONS LIST =================
@admin_bp.route("/reservations")
@login_required
@admin_required
def admin_reservations():
    status = request.args.get("status", "all")
    user_id = request.args.get("user_id")
    trainer_id = request.args.get("trainer_id")
    service_id = request.args.get("service_id")
    date = request.args.get("date")

    query = database.db_session.query(Reservation)

    if user_id:
        query = query.filter(Reservation.user_id == int(user_id))
    if trainer_id:
        query = query.filter(Reservation.trainer_id == int(trainer_id))
    if service_id:
        query = query.filter(Reservation.service_id == int(service_id))
    if date:
        query = query.filter(Reservation.date == date)

    reservations = query.order_by(Reservation.date, Reservation.time).all()

    now = datetime.now()
    enriched = []

    for r in reservations:
        raw = f"{r.date} {r.time}"
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
        except ValueError:
            dt = datetime.strptime(raw, "%d.%m.%Y %H:%M")

        if r.status == "canceled":
            derived = "canceled"
        elif dt.date() == now.date():
            derived = "today"
        elif dt < now:
            derived = "past"
        else:
            derived = "upcoming"

        r.ui_status = derived

        if status == "all" or derived == status:
            enriched.append(r)

    return render_template(
        "admin/reservations.html",
        reservations=enriched,
        users=database.db_session.query(User).all(),
        trainers=database.db_session.query(Trainer).all(),
        services=database.db_session.query(Service).all(),
        active="admin",
        selected={
            "status": status,
            "user_id": user_id or "",
            "trainer_id": trainer_id or "",
            "service_id": service_id or "",
            "date": date or "",
        },
    )


# ================= RESERVATION PARTIAL (HTMX) =================
@admin_bp.route("/reservations/partial")
@login_required
@admin_required
def reservations_partial():
    q = request.args.get("q", "").lower()
    status = request.args.get("status", "all")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    query = database.db_session.query(Reservation)

    if q:
        query = (
            query.join(User)
            .join(Trainer)
            .join(Service)
            .filter(
                func.lower(User.login).like(f"%{q}%")
                | func.lower(User.email).like(f"%{q}%")
                | func.lower(Trainer.name).like(f"%{q}%")
                | func.lower(Service.name).like(f"%{q}%")
            )
        )

    reservations = query.order_by(Reservation.date, Reservation.time).all()

    now = datetime.now()
    enriched = []

    for r in reservations:
        raw = f"{r.date} {r.time}"
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
        except ValueError:
            dt = datetime.strptime(raw, "%d.%m.%Y %H:%M")

        if r.status == "canceled":
            derived = "canceled"
        elif dt.date() == now.date():
            derived = "today"
        elif dt < now:
            derived = "past"
        else:
            derived = "upcoming"

        r.ui_status = derived

        if status == "all" or derived == status:
            enriched.append(r)

    total = len(enriched)
    total_pages = max(1, ceil(total / per_page))

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None

    start = (page - 1) * per_page
    enriched = enriched[start:start + per_page]

    return render_template(
        "admin/partials/reservations_table.html",
        reservations=enriched,
        page=page,
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page,
        q=q,
        status=status,
        per_page=per_page,
    )


# ================= RESERVATION DETAILS =================
@admin_bp.route("/reservations/<int:res_id>")
@login_required
@admin_required
def reservation_detail(res_id):
    r = database.db_session.get(Reservation, res_id)
    return render_template("admin/reservation_detail.html", r=r, error=None)


# ====== RESCHEDULE ======
@admin_bp.route("/reservations/<int:res_id>/reschedule", methods=["POST"])
@login_required
@admin_required
def reservation_reschedule(res_id):
    r = database.db_session.get(Reservation, res_id)

    new_date = request.form["date"]
    new_time = request.form["time"]

    conflict = (
        database.db_session.query(Reservation)
        .filter(
            Reservation.trainer_id == r.trainer_id,
            Reservation.date == new_date,
            Reservation.time == new_time,
            Reservation.id != res_id,
        )
        .first()
    )

    if conflict:
        return render_template(
            "admin/reservation_detail.html",
            r=r,
            error="Trainer already has reservation at this time.",
        )

    r.date = new_date
    r.time = new_time
    database.db_session.commit()

    asyncio.run(notify_reservation_update(r, "rescheduled"))

    return redirect(f"/admin/reservations/{res_id}")


# ====== CANCEL ======
@admin_bp.route("/reservations/<int:res_id>/cancel", methods=["POST"])
@login_required
@admin_required
def reservation_cancel(res_id):
    r = database.db_session.get(Reservation, res_id)
    r.status = "canceled"
    database.db_session.commit()

    asyncio.run(notify_reservation_update(r, "canceled"))

    return redirect(f"/admin/reservations/{res_id}")


# ====== RESTORE ======
@admin_bp.route("/reservations/<int:res_id>/restore", methods=["POST"])
@login_required
@admin_required
def reservation_restore(res_id):
    r = database.db_session.get(Reservation, res_id)
    r.status = "active"
    database.db_session.commit()

    asyncio.run(notify_reservation_update(r, "restored"))

    return redirect(f"/admin/reservations/{res_id}")


# ================= CALENDAR =================
@admin_bp.route("/reservations/calendar")
@login_required
@admin_required
def reservations_calendar():
    reservations = database.db_session.query(Reservation).all()
    return render_template("admin/calendar.html", reservations=reservations)


# ================= EXPORT EXCEL =================
@admin_bp.route("/reservations/export")
@login_required
@admin_required
def reservations_export():
    reservations = database.db_session.query(Reservation).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Reservations"

    ws.append(["ID", "User login", "User email", "Trainer", "Service", "Date", "Status"])

    for r in reservations:
        ws.append([
            r.id,
            r.user.login if r.user else "",
            r.user.email if r.user else "",
            r.trainer.name if r.trainer else "",
            r.service.name if r.service else "",
            f"{r.date} {r.time}",
            r.status,
        ])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    return send_file(
        stream,
        as_attachment=True,
        download_name="reservations.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ================= RESERVATION LOG =================
@admin_bp.route("/reservations/<int:res_id>/log")
@login_required
@admin_required
def reservation_log(res_id):
    logs = (
        database.db_session.query(AuditLog)
        .filter(AuditLog.entity == "reservation", AuditLog.entity_id == res_id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return render_template("admin/reservation_log.html", logs=logs, res_id=res_id)


# ================= USERS =================
@admin_bp.route("/users")
@login_required
@admin_required
def admin_users():
    users = database.db_session.query(User).order_by(User.id).all()
    return render_template("admin/users.html", users=users, active="admin")


@admin_bp.route("/users/<int:user_id>")
@login_required
@admin_required
def admin_user_detail(user_id):
    user = database.db_session.get(User, user_id)
    reservations = (
        database.db_session.query(Reservation).filter_by(user_id=user_id).all()
    )
    return render_template(
        "admin/user_detail.html",
        user=user,
        reservations=reservations,
        active="admin",
    )


@admin_bp.route("/users/<int:user_id>/ban", methods=["POST"])
@login_required
@admin_required
def admin_ban_user(user_id):
    user = database.db_session.get(User, user_id)
    if user:
        user.is_banned = True
        database.db_session.commit()
        log_action("ban", "user", user.id)

    return redirect("/admin/users")


@admin_bp.route("/users/<int:user_id>/unban", methods=["POST"])
@login_required
@admin_required
def admin_unban_user(user_id):
    user = database.db_session.get(User, user_id)
    if user:
        user.is_banned = False
        database.db_session.commit()
        log_action("unban", "user", user.id)

    return redirect("/admin/users")


# ================= AUDIT LOG PAGE =================
@admin_bp.route("/logs")
@login_required
@admin_required
def admin_logs():
    logs = (
        database.db_session.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(100)
        .all()
    )
    return render_template("admin/logs.html", logs=logs, active="admin")
