import re

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Appointment, Employee, User, Vehicle, Review
from sqlalchemy import func

admin = Blueprint("admin", __name__, url_prefix="/admin")

def normalize_phone_number(phone):
    phone = re.sub(r"[\s\-()]", "", phone)

    if phone.startswith("+359"):
        phone = "0" + phone[4:]
    elif phone.startswith("00359"):
        phone = "0" + phone[5:]

    return phone


def is_valid_phone_number(phone):
    return re.fullmatch(r"0\d{8,9}", phone) is not None


def find_existing_employee_phone(phone, exclude_id=None):
    query = Employee.query

    if exclude_id is not None:
        query = query.filter(Employee.id != exclude_id)

    for employee in query.all():
        if employee.phone and normalize_phone_number(
            employee.phone
        ) == phone:
            return employee

    return None

@admin.route("/dashboard")
@login_required
def dashboard():
    admin_required()

    total_customers = User.query.filter_by(role="customer").count()

    total_vehicles = Vehicle.query.count()

    total_appointments = Appointment.query.count()

    completed_appointments = Appointment.query.filter_by(status="completed").count()

    avrage_rating = db.session.query(func.avg(Review.rating)).scalar()

    return render_template(
        "admin/dashboard.html",
        total_customers=total_customers,
        total_vehicles=total_vehicles,
        total_appointments=total_appointments,
        completed_appointments=completed_appointments,
        average_rating=avrage_rating
    )


def admin_required():
    if current_user.role != "admin":
        abort(403)


@admin.route("/appointments")
@login_required
def appointments():
    admin_required()

    status_filter = request.args.get("status", "all")

    query = Appointment.query

    if status_filter != "all":
        query = query.filter_by(status=status_filter)

    all_appointments = query.order_by(
        Appointment.appointment_date.desc()
    ).all()

    active_employees = Employee.query.filter_by(
        is_active=True
    ).order_by(Employee.name).all()

    return render_template(
        "admin/appointments.html",
        appointments=all_appointments,
        status_filter=status_filter,
        employees=active_employees,
    )

@admin.route(
    "/appointments/<int:appointment_id>/assign",
    methods=["POST"]
)
@login_required
def assign_employee(appointment_id):
    admin_required()

    appointment = db.session.get(Appointment, appointment_id)

    if appointment is None:
        abort(404)

    employee_id = request.form.get("employee_id", "").strip()

    if employee_id == "":
        appointment.employee_id = None
    else:
        try:
            employee_id = int(employee_id)
        except ValueError:
            flash("Невалиден служител.", "danger")
            return redirect(url_for("admin.appointments"))

        employee = Employee.query.filter_by(
            id=employee_id,
            is_active=True
        ).first()

        if employee is None:
            flash("Избраният служител не е активен или не съществува.", "danger")
            return redirect(url_for("admin.appointments"))

        appointment.employee_id = employee.id

    db.session.commit()

    flash("Служителят беше назначен успешно.", "success")

    return redirect(
        url_for(
            "admin.appointments",
            status=request.form.get("status_filter", "all")
        )
    )

@admin.route("/appointments/<int:appointment_id>/status", methods=["POST"])
@login_required
def update_appointment_status(appointment_id):
    admin_required()

    appointment = db.session.get(Appointment, appointment_id)

    if appointment is None:
        abort(404)

    new_status = request.form.get("status")

    allowed_statuses = ["pending", "approved", "rejected", "completed"]

    if new_status not in allowed_statuses:
        flash("Невалиден статус.", "danger")
        return redirect(url_for("admin.appointments"))

    appointment.status = new_status
    db.session.commit()

    flash("Статусът на заявката беше променен успешно.", "success")

    return redirect(url_for("admin.appointments"))

@admin.route("/employees", methods=["GET", "POST"])
@login_required
def employees():
    admin_required()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        position = request.form.get("position", "").strip()
        phone = normalize_phone_number(
        request.form.get("phone", "")
    )

        if not name or not position or not phone:
            flash("Името, длъжността и телефонът са задължителни.", "danger")

        elif not is_valid_phone_number(phone):
            flash("Невалиден телефонен номер! Въведете български номер с 9 или 10 цифри.", "danger")

        elif find_existing_employee_phone(phone):
            flash("Служител с този телефонен номер вече съществува.", "danger")

        else:
            employee = Employee(
                name=name,
                position=position,
                phone=phone,
                is_active=True
            )

            db.session.add(employee)
            db.session.commit()

            flash("Служителят беше добавен успешно!", "success")
            return redirect(url_for("admin.employees"))

    all_employees = Employee.query.order_by(Employee.name).all()

    return render_template(
        "admin/employees.html",
        employees=all_employees
    )


@admin.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    admin_required()

    employee = db.session.get(Employee, employee_id)

    if employee is None:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        position = request.form.get("position", "").strip()
        phone = normalize_phone_number(request.form.get("phone", ""))

        if not name or not position or not phone:
            flash("Името, длъжността и телефонът са задължителни.", "danger")
        elif not is_valid_phone_number(phone):
            flash("Невалиден телефонен номер! Въведете български номер с 9 или 10 цифри.", "danger")

        elif find_existing_employee_phone(phone, exclude_id=employee.id):
            flash("Служител с този телефонен номер вече съществува.", "danger")
        else:
            employee.name = name
            employee.position = position
            employee.phone = phone

            db.session.commit()

            flash("Информацията за служителя е обновена.", "success")
            return redirect(url_for("admin.employees"))

    return render_template(
        "admin/edit_employee.html",
        employee=employee
    )


@admin.route("/employees/<int:employee_id>/toggle", methods=["POST"])
@login_required
def toggle_employee(employee_id):
    admin_required()

    employee = db.session.get(Employee, employee_id)

    if employee is None:
        abort(404)

    employee.is_active = not employee.is_active

    db.session.commit()

    flash("Статусът на служителя беше променен.", "success")

    return redirect(url_for("admin.employees"))
