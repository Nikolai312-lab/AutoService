from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.extensions import db
from app.models import User

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Моля, попълнете всички задължителни полета.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Паролите не съвпадат.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Паролата трябва да бъде поне 8 символа.", "danger")
            return render_template("auth/register.html")

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Това потребителско име или имейл вече се използва.", "danger")
            return render_template("auth/register.html")

        user = User(
            username=username,
            email=email,
            role="customer"
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Регистрацията е успешна!", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Успешно влязохте в профила си!", "success")
            return redirect(url_for("main.index"))

        flash("Невалиден имейл или парола.", "danger")

    return render_template("auth/login.html")


@auth.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Излязохте от профила си.", "success")

    return redirect(url_for("main.index"))