
from app.extensions import db
from app.models import User, Vehicle


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


def create_vehicle(user_id, registration_number="CB1234AB"):
    vehicle = Vehicle(
        brand="Toyota",
        model="Corolla",
        registration_number=registration_number,
        year=2020,
        owner_id=user_id,
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle


def login(client, email):
    return client.post(
        "/auth/login",
        data={
            "email": email,
            "password": "password123",
        },
    )


def test_vehicles_require_login(client):
    response = client.get("/vehicles/")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_add_vehicle(client, app):
    with app.app_context():
        create_user("owner", "owner@example.com")

    login(client, "owner@example.com")

    response = client.post(
        "/vehicles/add",
        data={
            "brand": "BMW",
            "model": "320d",
            "registration_number": "cb1234ab",
            "year": "2021",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Автомобилът беше добавен успешно!" in response.get_data(as_text=True)

    with app.app_context():
        vehicle = Vehicle.query.filter_by(
            registration_number="СВ1234АВ"
        ).first()
        assert vehicle is not None
        assert vehicle.brand == "BMW"
        assert vehicle.year == 2021


def test_add_vehicle_invalid_year(client, app):
    with app.app_context():
        create_user("owner", "owner@example.com")

    login(client, "owner@example.com")

    response = client.post(
        "/vehicles/add",
        data={
            "brand": "BMW",
            "model": "320d",
            "registration_number": "CB1234AB",
            "year": "1800",
        },
    )

    assert response.status_code == 200
    assert "Моля, въведете валидна година." in response.get_data(as_text=True)


def test_add_duplicate_registration_number(client, app):
    with app.app_context():
        user = create_user("owner", "owner@example.com")
        create_vehicle(user.id)

    login(client, "owner@example.com")

    response = client.post(
        "/vehicles/add",
        data={
            "brand": "BMW",
            "model": "320d",
            "registration_number": "CB1234AB",
            "year": "2021",
        },
    )

    assert response.status_code == 200
    assert "Автомобил с този регистрационен номер вече съществува." in response.get_data(as_text=True)


def test_vehicle_list_shows_only_own_vehicles(client, app):
    with app.app_context():
        owner = create_user("owner", "owner@example.com")
        other = create_user("other", "other@example.com")

        create_vehicle(owner.id, "CB1111AA")
        create_vehicle(other.id, "CB2222BB")

    login(client, "owner@example.com")

    response = client.get("/vehicles/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "CB1111AA" in page
    assert "CB2222BB" not in page


def test_edit_vehicle(client, app):
    with app.app_context():
        user = create_user("owner", "owner@example.com")
        vehicle = create_vehicle(user.id)
        vehicle_id = vehicle.id

    login(client, "owner@example.com")

    response = client.post(
        f"/vehicles/edit/{vehicle_id}",
        data={
            "brand": "Audi",
            "model": "A4",
            "registration_number": "CB9999CC",
            "year": "2022",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Автомобилът беше редактиран успешно!" in response.get_data(as_text=True)

    with app.app_context():
        vehicle = db.session.get(Vehicle, vehicle_id)
        assert vehicle.brand == "Audi"
        assert vehicle.model == "A4"
        assert vehicle.registration_number == "СВ9999СС"
        assert vehicle.year == 2022


def test_cannot_edit_another_users_vehicle(client, app):
    with app.app_context():
        owner = create_user("owner", "owner@example.com")
        other = create_user("other", "other@example.com")
        vehicle = create_vehicle(owner.id)
        vehicle_id = vehicle.id

    login(client, "other@example.com")

    response = client.post(
        f"/vehicles/edit/{vehicle_id}",
        data={
            "brand": "Audi",
            "model": "A4",
            "registration_number": "CB9999CC",
            "year": "2022",
        },
    )

    assert response.status_code == 404


def test_delete_vehicle(client, app):
    with app.app_context():
        user = create_user("owner", "owner@example.com")
        vehicle = create_vehicle(user.id)
        vehicle_id = vehicle.id

    login(client, "owner@example.com")

    response = client.post(f"/vehicles/delete/{vehicle_id}")

    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Vehicle, vehicle_id) is None


def test_cannot_delete_another_users_vehicle(client, app):
    with app.app_context():
        owner = create_user("owner", "owner@example.com")
        other = create_user("other", "other@example.com")
        vehicle = create_vehicle(owner.id)
        vehicle_id = vehicle.id

    login(client, "other@example.com")

    response = client.post(f"/vehicles/delete/{vehicle_id}")

    assert response.status_code == 404

    with app.app_context():
        assert db.session.get(Vehicle, vehicle_id) is not None
