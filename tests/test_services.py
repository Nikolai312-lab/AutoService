
from app.extensions import db
from app.models import Service


def create_service(name, is_active=True):
    service = Service(
        name=name,
        description=f"Описание на {name}",
        price=50.00,
        duration_minutes=60,
        is_active=is_active
    )

    db.session.add(service)
    db.session.commit()

    return service.id


def test_services_page_loads(client):
    response = client.get("/services/")

    assert response.status_code == 200


def test_services_page_shows_active_services(client, app):
    with app.app_context():
        create_service("Смяна на масло")
        create_service("Диагностика")

    response = client.get("/services/")

    assert response.status_code == 200

    page = response.get_data(as_text=True)

    assert "Смяна на масло" in page
    assert "Диагностика" in page


def test_services_page_hides_inactive_services(client, app):
    with app.app_context():
        create_service("Активна услуга")
        create_service("Неактивна услуга", is_active=False)

    response = client.get("/services/")

    page = response.get_data(as_text=True)

    assert "Активна услуга" in page
    assert "Неактивна услуга" not in page


def test_services_are_sorted_by_name(client, app):
    with app.app_context():
        create_service("Смяна на масло")
        create_service("Диагностика")
        create_service("Ремонт на двигател")

    response = client.get("/services/")

    page = response.get_data(as_text=True)

    first = page.index("Диагностика")
    second = page.index("Ремонт на двигател")
    third = page.index("Смяна на масло")

    assert first < second < third
