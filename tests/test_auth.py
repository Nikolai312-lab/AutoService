
from app.extensions import db
from app.models import User


def test_register_page(client):
    response = client.get("/auth/register")
    assert response.status_code == 200


def test_login_page(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_successful_registration(client, app):
    response = client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "TEST@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
        assert user.username == "testuser"
        assert user.role == "customer"
        assert user.check_password("password123")


def test_registration_password_mismatch(client):
    response = client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "different123",
        },
    )

    assert response.status_code == 200
    assert "Паролите не съвпадат." in response.get_data(as_text=True)


def test_registration_short_password(client):
    response = client.post(
        "/auth/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",
            "confirm_password": "123",
        },
    )

    assert response.status_code == 200
    assert "Паролата трябва да бъде поне 8 символа." in response.get_data(as_text=True)


def test_successful_login(client, app):
    with app.app_context():
        user = User(
            username="loginuser",
            email="login@example.com",
            role="customer",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/auth/login",
        data={
            "email": "LOGIN@example.com",
            "password": "password123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"loginuser" in response.data


def test_login_wrong_password(client, app):
    with app.app_context():
        user = User(
            username="loginuser",
            email="login@example.com",
            role="customer",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/auth/login",
        data={
            "email": "login@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 200
    assert "Невалиден имейл или парола." in response.get_data(as_text=True)


def test_logout(client, app):
    with app.app_context():
        user = User(
            username="logoutuser",
            email="logout@example.com",
            role="customer",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

    client.post(
        "/auth/login",
        data={
            "email": "logout@example.com",
            "password": "password123",
        },
    )

    response = client.get("/auth/logout")

    assert response.status_code == 302
    assert response.location.endswith("/")
