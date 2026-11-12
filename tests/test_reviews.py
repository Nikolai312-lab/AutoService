
from datetime import datetime

from app.extensions import db
from app.models import User, Vehicle, Service, Appointment, Review


def create_user(username, email, role="customer"):
    user = User(
        username=username,
        email=email,
        role=role
    )
    user.set_password("testpassword123")

    db.session.add(user)
    db.session.commit()

    return user


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def create_appointment(status="completed"):
    user = create_user(
        "review_customer",
        "review_customer@example.com"
    )

    vehicle = Vehicle(
        brand="BMW",
        model="320d",
        registration_number="CB1234AB",
        year=2020,
        owner_id=user.id
    )

    service = Service(
        name="Ремонт за тест",
        description="Тестова услуга",
        price=100.00,
        duration_minutes=60,
        is_active=True
    )

    db.session.add_all([vehicle, service])
    db.session.commit()

    appointment = Appointment(
        appointment_date=datetime(2099, 6, 15, 10, 0),
        status=status,
        description="Тестова заявка за ремонт",
        customer_id=user.id,
        vehicle_id=vehicle.id,
        service_id=service.id
    )

    db.session.add(appointment)
    db.session.commit()

    return user.id, appointment.id


def test_reviews_require_login(client):
    response = client.get("/reviews/")

    assert response.status_code == 302


def test_customer_can_open_review_page(client, app):
    with app.app_context():
        user_id, appointment_id = create_appointment()

    login_as(client, user_id)

    response = client.get(
        f"/reviews/appointment/{appointment_id}"
    )

    assert response.status_code == 200


def test_customer_cannot_review_another_users_appointment(client, app):
    with app.app_context():
        _, appointment_id = create_appointment()

        other_user = create_user(
            "other_customer",
            "other@example.com"
        )
        other_user_id = other_user.id

    login_as(client, other_user_id)

    response = client.get(
        f"/reviews/appointment/{appointment_id}"
    )

    assert response.status_code == 403


def test_customer_cannot_review_uncompleted_appointment(client, app):
    with app.app_context():
        user_id, appointment_id = create_appointment(
            status="pending"
        )

    login_as(client, user_id)

    response = client.get(
        f"/reviews/appointment/{appointment_id}"
    )

    assert response.status_code == 302


def test_customer_can_submit_review(client, app):
    with app.app_context():
        user_id, appointment_id = create_appointment()

    login_as(client, user_id)

    response = client.post(
        f"/reviews/appointment/{appointment_id}",
        data={
            "rating": "5",
            "comment": "Отлично обслужване!"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        review = Review.query.filter_by(
            appointment_id=appointment_id
        ).first()

        assert review is not None
        assert review.rating == 5
        assert review.comment == "Отлично обслужване!"
        assert review.customer_id == user_id


def test_customer_cannot_submit_invalid_rating(client, app):
    with app.app_context():
        user_id, appointment_id = create_appointment()

    login_as(client, user_id)

    response = client.post(
        f"/reviews/appointment/{appointment_id}",
        data={
            "rating": "6",
            "comment": "Невалидна оценка"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        review = Review.query.filter_by(
            appointment_id=appointment_id
        ).first()

        assert review is None


def test_customer_cannot_submit_second_review(client, app):
    with app.app_context():
        user_id, appointment_id = create_appointment()

        review = Review(
            rating=4,
            comment="Първа оценка",
            customer_id=user_id,
            appointment_id=appointment_id
        )

        db.session.add(review)
        db.session.commit()

    login_as(client, user_id)

    response = client.post(
        f"/reviews/appointment/{appointment_id}",
        data={
            "rating": "5",
            "comment": "Втора оценка"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        reviews = Review.query.filter_by(
            appointment_id=appointment_id
        ).all()

        assert len(reviews) == 1
        assert reviews[0].rating == 4


def test_customer_cannot_access_all_reviews(client, app):
    with app.app_context():
        user = create_user(
            "regular_customer",
            "regular@example.com"
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.get("/reviews/")

    assert response.status_code == 403


def test_admin_can_view_all_reviews(client, app):
    with app.app_context():
        admin = create_user(
            "review_admin",
            "review_admin@example.com",
            role="admin"
        )
        admin_id = admin.id

        user_id, appointment_id = create_appointment()

        review = Review(
            rating=5,
            comment="Много добро обслужване",
            customer_id=user_id,
            appointment_id=appointment_id
        )

        db.session.add(review)
        db.session.commit()

    login_as(client, admin_id)

    response = client.get("/reviews/")

    assert response.status_code == 200
    assert "Много добро обслужване" in response.get_data(as_text=True)
