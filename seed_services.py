from app import create_app
from app.extensions import db
from app.models import Service

app = create_app()

initial_services = [
    {
        "name": "Смяна на масло",
        "description": "Смяна на двигателно масло и маслен филтър.",
        "price": 80.00,
        "duration_minutes": 45
    },
    {
        "name": "Компютърна диагностика",
        "description": "Проверка на автомобила с диагностичен уред.",
        "price": 50.00,
        "duration_minutes": 30
    },
    {
        "name": "Смяна на спирачни накладки",
        "description": "Проверка и смяна на спирачните накладки.",
        "price": 120.00,
        "duration_minutes": 90
    },
    {
        "name": "Смяна на гуми",
        "description": "Демонтаж и монтаж на автомобилни гуми.",
        "price": 60.00,
        "duration_minutes": 40
    },
    {
        "name": "Проверка на климатик",
        "description": "Проверка на климатичната система.",
        "price": 40.00,
        "duration_minutes": 30
    },
    {
        "name": "Обслужване на ходова част",
        "description": "Проверка на окачването и ходовата част.",
        "price": 100.00,
        "duration_minutes": 60
    }
]

with app.app_context():
    added = 0

    for data in initial_services:
        existing = Service.query.filter_by(name=data["name"]).first()

        if not existing:
            service = Service(**data)
            db.session.add(service)
            added += 1

    db.session.commit()

    print(f"Успешно добавени услуги: {added}")
    print(f"Общо активни услуги: {Service.query.filter_by(is_active=True).count()}")