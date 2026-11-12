from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Appointment, Vehicle, Service

appointments = Blueprint(
    "appointments",
    __name__,
    url_prefix="/appointments"
)


@appointments.route("/")
@login_required
def index():
    all_appointments = Appointment.query.filter_by(
        customer_id=current_user.id
    ).order_by(Appointment.appointment_date.desc()).all()

    return render_template(
        "appointments/index.html",
        appointments=all_appointments
    )


@appointments.route("/book", methods=["GET", "POST"])
@login_required
def book():
    user_vehicles = Vehicle.query.filter_by(
        owner_id=current_user.id
    ).all()

    available_services = Service.query.filter_by(
        is_active=True
    ).all()

    if not user_vehicles:
        flash("Първо трябва да добавите автомобил.", "warning")
        return redirect(url_for("vehicles.index"))

    if not available_services:
        flash("В момента няма налични услуги.", "warning")
        return redirect(url_for("services.index"))

    if request.method == "POST":
        try:
            vehicle_id = int(request.form.get("vehicle_id"))
            service_id = int(request.form.get("service_id"))
            appointment_date = datetime.fromisoformat(
                request.form.get("appointment_date")
            )
            description = request.form.get("description", "").strip()

            vehicle = Vehicle.query.filter_by(
                id=vehicle_id,
                owner_id=current_user.id
            ).first()

            service = Service.query.filter_by(
                id=service_id,
                is_active=True
            ).first()

            if not vehicle or not service:
                flash("Избраният автомобил или услуга е невалиден.", "danger")
                return render_template(
                    "appointments/book.html",
                    vehicles=user_vehicles,
                    services=available_services
                )

            if appointment_date <= datetime.now():
                flash("Изберете дата и час в бъдещето.", "danger")
                return render_template(
                    "appointments/book.html",
                    vehicles=user_vehicles,
                    services=available_services
                )

            existing_appointment = Appointment.query.filter_by(
                appointment_date=appointment_date,
            ).first()

            if existing_appointment:
                flash("Вече има заявка за час на избраната дата и час.", "danger")
                return render_template(
                    "appointments/book.html",
                    vehicles=user_vehicles,
                    services=available_services
                )

            appointment = Appointment(
                appointment_date=appointment_date,
                status="pending",
                description=description,
                customer_id=current_user.id,
                vehicle_id=vehicle.id,
                service_id=service.id
            )

            db.session.add(appointment)
            db.session.commit()

            flash("Заявката за час беше изпратена успешно!", "success")
            return redirect(url_for("appointments.index"))

        except (ValueError, TypeError):
            flash("Моля, проверете въведените данни.", "danger")

    return render_template(
        "appointments/book.html",
        vehicles=user_vehicles,
        services=available_services
    )