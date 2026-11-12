
from datetime import UTC, datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    vehicles = db.relationship(
        "Vehicle", back_populates="owner",
        cascade="all, delete-orphan"
    )

    appointments = db.relationship(
        "Appointment", back_populates="customer"
    )

    reviews = db.relationship(
        "Review", back_populates="customer"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    registration_number = db.Column(
        db.String(20), unique=True, nullable=False
    )
    year = db.Column(db.Integer, nullable=False)

    owner_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    owner = db.relationship("User", back_populates="vehicles")

    appointments = db.relationship(
        "Appointment", back_populates="vehicle"
    )

    def __repr__(self):
        return f"<Vehicle {self.brand} {self.model}>"


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    appointments = db.relationship(
        "Appointment", back_populates="service"
    )

    def __repr__(self):
        return f"<Service {self.name}>"


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(30))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    appointments = db.relationship(
        "Appointment", back_populates="employee"
    )

    def __repr__(self):
        return f"<Employee {self.name}>"


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    appointment_date = db.Column(db.DateTime, nullable=False, unique=True)
    status = db.Column(
        db.String(30), nullable=False, default="pending"
    )
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    customer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    vehicle_id = db.Column(
        db.Integer, db.ForeignKey("vehicles.id"), nullable=False
    )

    service_id = db.Column(
        db.Integer, db.ForeignKey("services.id"), nullable=False
    )

    employee_id = db.Column(
        db.Integer, db.ForeignKey("employees.id"), nullable=True
    )

    customer = db.relationship(
        "User", back_populates="appointments"
    )

    vehicle = db.relationship(
        "Vehicle", back_populates="appointments"
    )

    service = db.relationship(
        "Service", back_populates="appointments"
    )

    employee = db.relationship(
        "Employee", back_populates="appointments"
    )

    review = db.relationship(
        "Review", back_populates="appointment",
        uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Appointment {self.id}: {self.status}>"


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    customer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointments.id"),
        unique=True,
        nullable=False
    )

    customer = db.relationship(
        "User", back_populates="reviews"
    )

    appointment = db.relationship(
        "Appointment", back_populates="review"
    )

    __table_args__ = (
        db.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="check_review_rating"
        ),
    )

    def __repr__(self):
        return f"<Review {self.rating}/5>"
