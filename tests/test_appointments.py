
from datetime import datetime

from app.extensions import db
from app.models import User, Vehicle, Service, Appointment


def create_user(username, email):
    user = User(
        username=username,
        email=email,
        role="customer",
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


def create_vehicle(user_id):
    vehicle = Vehicle(
        brand="Toyota",
        model="Corolla",
        registration_number="CB1234AB",
        year=2020,
        owner_id=user_id,
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle


def create_service(is_active=True, name = "Смяна на масло"):
    service = Service(
        name=name,
        description="Тестова услуга",
        price=50.00,
        duration_minutes=60,
        is_active=is_active,
    )
    db.session.add(service)
    db.session.flush()
    return service


def login(client, email):
    return client.post(
        "/auth/login",
        data={
            "email": email,
            "password": "password123",
        },
    )


def test_appointments_require_login(client):
    response = client.get("/appointments/")

    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_booking_without_vehicle(client, app):
    with app.app_context():
        create_user("customer", "customer@example.com")
        create_service()

    login(client, "customer@example.com")

    response = client.get("/appointments/book")

    assert response.status_code == 302
    assert response.location.endswith("/vehicles/")


def test_booking_without_active_services(client, app):
    with app.app_context():
        user = create_user("customer", "customer@example.com")
        create_vehicle(user.id)
        create_service(is_active=False)

    login(client, "customer@example.com")

    response = client.get("/appointments/book")

    assert response.status_code == 302
    assert response.location.endswith("/services/")


def test_successful_appointment_booking(client, app):
    with app.app_context():
        user = create_user("customer", "customer@example.com")
        vehicle = create_vehicle(user.id)
        service = create_service()

        vehicle_id = vehicle.id
        service_id = service.id

        db.session.commit()

    login(client, "customer@example.com")

    response = client.post(
        "/appointments/book",
        data={
            "vehicle_id": str(vehicle_id),
            "service_id": str(service_id),
            "appointment_date": "2099-06-15T10:00",
            "description": "Проверка на автомобила",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Заявката за час беше изпратена успешно!" in response.get_data(as_text=True)

    with app.app_context():
        appointment = Appointment.query.first()

        assert appointment is not None
        assert appointment.status == "pending"
        assert appointment.customer_id is not None
        assert appointment.description == "Проверка на автомобила"


def test_booking_past_date(client, app):
    with app.app_context():
        user = create_user("customer", "customer@example.com")
        vehicle = create_vehicle(user.id)
        service = create_service()

        vehicle_id = vehicle.id
        service_id = service.id

        db.session.commit()

    login(client, "customer@example.com")

    response = client.post(
        "/appointments/book",
        data={
            "vehicle_id": str(vehicle_id),
            "service_id": str(service_id),
            "appointment_date": "2000-01-01T10:00",
            "description": "Тест",
        },
    )

    assert response.status_code == 200
    assert "Изберете дата и час в бъдещето." in response.get_data(as_text=True)

    with app.app_context():
        assert Appointment.query.count() == 0


def test_cannot_book_with_another_users_vehicle(client, app):
    with app.app_context():
        customer = create_user("customer", "customer@example.com")
        other_user = create_user("other", "other@example.com")

        # Клиентът има собствен автомобил.
        own_vehicle = Vehicle(
            brand="Ford",
            model="Focus",
            registration_number="CB1111AA",
            year=2020,
            owner_id=customer.id,
        )
        db.session.add(own_vehicle)

        # Другият потребител има отделен автомобил.
        other_vehicle = create_vehicle(other_user.id)
        service = create_service()

        db.session.commit()

        vehicle_id = other_vehicle.id
        service_id = service.id

    login(client, "customer@example.com")

    response = client.post(
        "/appointments/book",
        data={
            "vehicle_id": str(vehicle_id),
            "service_id": str(service_id),
            "appointment_date": "2099-06-15T10:00",
            "description": "Тест",
        },
    )

    assert response.status_code == 200
    assert "Избраният автомобил или услуга е невалиден." in response.get_data(as_text=True)

    with app.app_context():
        assert Appointment.query.count() == 0


def test_cannot_book_inactive_service(client, app):
    with app.app_context():
        user = create_user("customer", "customer@example.com")
        vehicle = create_vehicle(user.id)

        # Добавяме активна услуга, за да преминем първоначалната проверка.
        create_service(is_active=True, name="Активна услуга")

        # Тази услуга ще бъде изпратена във формата.
        inactive_service = create_service(is_active=False, name="Неактивна услуга")

        vehicle_id = vehicle.id
        service_id = inactive_service.id

        db.session.commit()

    login(client, "customer@example.com")

    response = client.post(
        "/appointments/book",
        data={
            "vehicle_id": str(vehicle_id),
            "service_id": str(service_id),
            "appointment_date": "2099-06-15T10:00",
            "description": "Тест",
        },
    )

    assert response.status_code == 200
    assert "Избраният автомобил или услуга е невалиден." in response.get_data(as_text=True)

    with app.app_context():
        assert Appointment.query.count() == 0

def test_cannot_book_same_datetime_but_can_book_next_day(client, app):
    with app.app_context():
        user = create_user("customer", "customer@example.com")
        vehicle = create_vehicle(user.id)
        service = create_service()

        db.session.commit()

        vehicle_id = vehicle.id
        service_id = service.id

    login(client, "customer@example.com")

    appointment_data = {
        "vehicle_id": str(vehicle_id),
        "service_id": str(service_id),
        "appointment_date": "2099-06-15T10:00",
        "description": "Test appointment",
    }

    # Първият запис трябва да бъде успешен.
    first_response = client.post(
        "/appointments/book",
        data=appointment_data,
        follow_redirects=True,
    )

    assert first_response.status_code == 200

    with app.app_context():
        assert Appointment.query.count() == 1, (
            first_response.get_data(as_text=True)
        )

    # Повторният запис за същата дата и час трябва да бъде отказан.
    duplicate_response = client.post(
        "/appointments/book",
        data=appointment_data,
        follow_redirects=True,
    )

    assert duplicate_response.status_code == 200

    with app.app_context():
        assert Appointment.query.count() == 1

    # Същият час на следващия ден трябва да бъде разрешен.
    next_day_data = appointment_data.copy()
    next_day_data["appointment_date"] = "2099-06-16T10:00"

    next_day_response = client.post(
        "/appointments/book",
        data=next_day_data,
        follow_redirects=True,
    )

    assert next_day_response.status_code == 200

    with app.app_context():
        assert Appointment.query.count() == 2
