import re

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Vehicle

vehicles = Blueprint("vehicles", __name__, url_prefix="/vehicles")

# Преобразува латинските букви, които изглеждат като
# българските букви върху регистрационните табели.
LATIN_TO_CYRILLIC = str.maketrans(
    "ABEKMHOPCTYX",
    "АВЕКМНОРСТУХ"
)


def normalize_registration_number(value):
    value = value.upper().translate(LATIN_TO_CYRILLIC)
    return re.sub(r"[\s-]", "", value)


def is_valid_registration_number(value):
    pattern = r"^[АВЕКМНОРСТУХ]{1,2}\d{4}[АВЕКМНОРСТУХ]{1,2}$"
    return re.fullmatch(pattern, value) is not None


def find_existing_vehicle(registration_number, exclude_id=None):
    query = Vehicle.query

    if exclude_id is not None:
        query = query.filter(Vehicle.id != exclude_id)

    return next(
        (
            vehicle for vehicle in query.all()
            if normalize_registration_number(
                vehicle.registration_number
            ) == registration_number
        ),
        None
    )


@vehicles.route("/")
@login_required
def index():
    user_vehicles = Vehicle.query.filter_by(
        owner_id=current_user.id
    ).all()

    return render_template(
        "vehicles/index.html",
        vehicles=user_vehicles
    )


@vehicles.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        brand = request.form.get("brand", "").strip()
        model = request.form.get("model", "").strip()
        registration_number = normalize_registration_number(
            request.form.get("registration_number", "")
        )
        year = request.form.get("year", "").strip()

        if not brand or not model or not registration_number or not year:
            flash("Моля, попълнете всички полета.", "danger")
            return render_template("vehicles/add.html")

        try:
            year = int(year)
            if year < 1886 or year > 2100:
                raise ValueError
        except ValueError:
            flash("Моля, въведете валидна година.", "danger")
            return render_template("vehicles/add.html")

        registration_number = normalize_registration_number(
            request.form.get("registration_number", "")
        )

        if not is_valid_registration_number(registration_number):
            flash(
                "Невалиден регистрационен номер! "
                "Използвайте формат с 1-2 букви, 4 цифри "
                "и 1-2 букви. Например: СВ1234АВ.",
                "danger"
            )
            return render_template("vehicles/add.html")

        existing_vehicle = find_existing_vehicle(registration_number)

        if existing_vehicle:
            flash("Автомобил с този регистрационен номер вече съществува.", "danger")
            return render_template("vehicles/add.html")

        vehicle = Vehicle(
            brand=brand,
            model=model,
            registration_number=registration_number,
            year=year,
            owner_id=current_user.id
        )

        db.session.add(vehicle)
        db.session.commit()

        flash("Автомобилът беше добавен успешно!", "success")
        return redirect(url_for("vehicles.index"))

    return render_template("vehicles/add.html")

@vehicles.route("/edit/<int:vehicle_id>", methods=["GET", "POST"])
@login_required
def edit(vehicle_id):
    vehicle = Vehicle.query.filter_by(
        id=vehicle_id,
        owner_id=current_user.id
    ).first_or_404()

    if request.method == "POST":
        brand = request.form.get("brand", "").strip()
        model = request.form.get("model", "").strip()
        registration_number = request.form.get(
            "registration_number", ""
        ).strip().upper()
        year = request.form.get("year", "").strip()

        if not brand or not model or not registration_number or not year:
            flash("Моля, попълнете всички полета.", "danger")
            return render_template("vehicles/edit.html", vehicle=vehicle)

        try:
            year = int(year)
            if year < 1886 or year > 2100:
                raise ValueError
        except ValueError:
            flash("Моля, въведете валидна година.", "danger")
            return render_template("vehicles/edit.html", vehicle=vehicle)

        registration_number = normalize_registration_number(
            request.form.get("registration_number", "")
        )

        if not is_valid_registration_number(registration_number):
            flash(
                "Невалиден регистрационен номер! "
                "Използвайте формат с 1-2 букви, 4 цифри "
                "и 1-2 букви. Например: СВ1234АВ.",
                "danger"
            )
            return render_template("vehicles/edit.html", vehicle=vehicle)

        existing_vehicle = find_existing_vehicle(
            registration_number,
            exclude_id=vehicle.id
        )

        if existing_vehicle:
            flash("Този регистрационен номер вече се използва.", "danger")
            return render_template("vehicles/edit.html", vehicle=vehicle)

        vehicle.brand = brand
        vehicle.model = model
        vehicle.registration_number = registration_number
        vehicle.year = year

        db.session.commit()

        flash("Автомобилът беше редактиран успешно!", "success")
        return redirect(url_for("vehicles.index"))

    return render_template("vehicles/edit.html", vehicle=vehicle)


@vehicles.route("/delete/<int:vehicle_id>", methods=["POST"])
@login_required
def delete(vehicle_id):
    vehicle = Vehicle.query.filter_by(
        id=vehicle_id,
        owner_id=current_user.id
    ).first_or_404()

    db.session.delete(vehicle)
    db.session.commit()

    flash("Автомобилът беше изтрит успешно!", "success")
    return redirect(url_for("vehicles.index"))