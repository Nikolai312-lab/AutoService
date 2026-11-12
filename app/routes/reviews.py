
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Review, Appointment

reviews = Blueprint("reviews", __name__, url_prefix="/reviews")


@reviews.route("/appointment/<int:appointment_id>", methods=["GET", "POST"])
@login_required
def add_review(appointment_id):
    appointment = db.session.get(Appointment,appointment_id)
    if appointment is None:
        abort(404)

    # Проверяваме дали часът принадлежи на текущия клиент
    if appointment.customer_id != current_user.id:
        abort(403)

    # Оценка може да се остави само за приключен ремонт
    if appointment.status != "completed":
        flash("Можете да оцените само приключен ремонт.", "warning")
        return redirect(url_for("appointments.index"))

    # Проверяваме дали вече има оценка
    existing_review = Review.query.filter_by(
        appointment_id=appointment.id
    ).first()

    if existing_review:
        flash("Вече сте оставили оценка за този ремонт.", "warning")
        return redirect(url_for("appointments.index"))

    if request.method == "POST":
        try:
            rating = int(request.form.get("rating", 0))
        except (ValueError, TypeError):
            rating = 0

        comment = request.form.get("comment", "").strip()

        if rating < 1 or rating > 5:
            flash("Оценката трябва да бъде между 1 и 5 звезди.", "danger")
            return redirect(
                url_for("reviews.add_review", appointment_id=appointment.id)
            )

        review = Review(
            rating=rating,
            comment=comment,
            customer_id=current_user.id,
            appointment_id=appointment.id
        )

        db.session.add(review)
        db.session.commit()

        flash("Благодарим за вашата оценка!", "success")
        return redirect(url_for("appointments.index"))

    return render_template(
        "reviews/add.html",
        appointment=appointment
    )


@reviews.route("/")
@login_required
def index():
    if current_user.role != "admin":
        abort(403)

    all_reviews = Review.query.order_by(
        Review.created_at.desc()
    ).all()

    return render_template(
        "admin/reviews.html",
        reviews=all_reviews
    )
