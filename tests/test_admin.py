from datetime import datetime

from app.extensions import db
from app.models import User, Appointment, Vehicle, Service, Employee


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

def create_appointment():
    user = create_user(
        "appointment_customer",
        "appointment@example.com"
    )

    vehicle = Vehicle(
        brand="BMW",
        model="320d",
        registration_number="CB1234AB",
        year=2020,
        owner_id=user.id
    )

    service = Service(
        name="Смяна на масло",
        description="Тестова услуга",
        price=50.00,
        duration_minutes=60,
        is_active=True
    )

    db.session.add_all([vehicle, service])
    db.session.commit()

    appointment = Appointment(
        appointment_date=datetime(2099, 6, 15, 10, 0),
        status="pending",
        description="Тестова заявка",
        customer_id=user.id,
        vehicle_id=vehicle.id,
        service_id=service.id
    )

    db.session.add(appointment)
    db.session.commit()

    return appointment.id


def create_employee(name="Иван Петров", is_active=True):
    employee = Employee(
        name=name,
        position="Механик",
        phone="0888123456",
        is_active=is_active
    )

    db.session.add(employee)
    db.session.commit()

    return employee.id

def test_admin_dashboard_requires_login(client):
    response = client.get("/admin/dashboard")

    assert response.status_code == 302


def test_customer_cannot_access_admin_dashboard(client, app):
    with app.app_context():
        user = create_user(
            "customer",
            "customer@example.com"
        )

        user_id = user.id

    login_as(client, user_id)

    response = client.get("/admin/dashboard")

    assert response.status_code == 403


def test_admin_can_access_dashboard(client, app):
    with app.app_context():
        user = create_user(
            "admin",
            "admin@example.com",
            role="admin"
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.get("/admin/dashboard")

    assert response.status_code == 200


def test_customer_cannot_access_admin_employees(client, app):
    with app.app_context():
        user = create_user(
            "customer",
            "customer@example.com"
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.get("/admin/employees")

    assert response.status_code == 403


def test_customer_cannot_access_admin_appointments(client, app):
    with app.app_context():
        user = create_user(
            "customer",
            "customer@example.com"
        )
        user_id = user.id
    login_as(client, user_id)

    response = client.get("/admin/appointments")

    assert response.status_code == 403

def test_admin_can_view_appointments(client, app):
    with app.app_context():
        user = create_user(
            "admin",
            "admin@example.com",
            role="admin"
        )
        create_appointment()
        user_id = user.id

    login_as(client, user_id)

    response = client.get("/admin/appointments")

    assert response.status_code == 200
    assert "Тестова заявка" in response.get_data(as_text=True)


def test_admin_can_filter_appointments(client, app):
    with app.app_context():
        user = create_user(
            "admin",
            "admin@example.com",
            role="admin"
        )
        appointment_id = create_appointment()

        appointment = db.session.get(Appointment, appointment_id)
        appointment.status = "completed"
        db.session.commit()

        user_id = user.id

    login_as(client, user_id)

    response = client.get("/admin/appointments?status=completed")

    assert response.status_code == 200
    assert "Тестова заявка" in response.get_data(as_text=True)


def test_admin_can_update_appointment_status(client, app):
    with app.app_context():
        user = create_user(
            "admin",
            "admin@example.com",
            role="admin"
        )
        appointment_id = create_appointment()
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/appointments/{appointment_id}/status",
        data={"status": "approved"}
    )

    assert response.status_code == 302

    with app.app_context():
        appointment = db.session.get(Appointment, appointment_id)
        assert appointment.status == "approved"


def test_admin_cannot_set_invalid_appointment_status(client, app):
    with app.app_context():
        user = create_user(
            "admin",
            "admin@example.com",
            role="admin"
        )
        appointment_id = create_appointment()
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/appointments/{appointment_id}/status",
        data={"status": "invalid_status"}
    )

    assert response.status_code == 302

    with app.app_context():
        appointment = db.session.get(Appointment, appointment_id)
        assert appointment.status == "pending"


def test_admin_can_assign_active_employee(client, app):
    with app.app_context():
        user = create_user(
            "admin",
            "admin@example.com",
            role="admin"
        )
        appointment_id = create_appointment()
        employee_id = create_employee()
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/appointments/{appointment_id}/assign",
        data={
            "employee_id": str(employee_id),
            "status_filter": "all"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        appointment = db.session.get(Appointment, appointment_id)
        assert appointment.employee_id == employee_id


def test_admin_cannot_assign_inactive_employee(client, app):
    with app.app_context():
        user = create_user(
            "admin",
            "admin@example.com",
            role="admin"
        )
        appointment_id = create_appointment()
        employee_id = create_employee(
            name="Неактивен служител",
            is_active=False
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/appointments/{appointment_id}/assign",
        data={
            "employee_id": str(employee_id)
        }
    )

    assert response.status_code == 302

    with app.app_context():
        appointment = db.session.get(Appointment, appointment_id)
        assert appointment.employee_id is None


def test_admin_can_view_employees(client, app):
    with app.app_context():
        user = create_user(
            "employee_admin",
            "employee_admin@example.com",
            role="admin"
        )
        create_employee(name="Иван Петров")
        user_id = user.id

    login_as(client, user_id)

    response = client.get("/admin/employees")

    assert response.status_code == 200
    assert "Иван Петров" in response.get_data(as_text=True)


def test_admin_can_add_employee(client, app):
    with app.app_context():
        user = create_user(
            "add_admin",
            "add_admin@example.com",
            role="admin"
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        "/admin/employees",
        data={
            "name": "Георги Иванов",
            "position": "Механик",
            "phone": "0888123456"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        employee = Employee.query.filter_by(
            name="Георги Иванов"
        ).first()

        assert employee is not None
        assert employee.position == "Механик"
        assert employee.phone == "0888123456"
        assert employee.is_active is True


def test_admin_cannot_add_employee_without_name(client, app):
    with app.app_context():
        user = create_user(
            "missing_name_admin",
            "missing_name@example.com",
            role="admin"
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        "/admin/employees",
        data={
            "name": "",
            "position": "Механик",
            "phone": "0888123456"
        }
    )

    assert response.status_code == 200

    with app.app_context():
        assert Employee.query.count() == 0


def test_admin_cannot_add_employee_without_position(client, app):
    with app.app_context():
        user = create_user(
            "missing_position_admin",
            "missing_position@example.com",
            role="admin"
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        "/admin/employees",
        data={
            "name": "Георги Иванов",
            "position": "",
            "phone": "0888123456"
        }
    )

    assert response.status_code == 200

    with app.app_context():
        assert Employee.query.count() == 0


def test_admin_can_open_employee_edit_page(client, app):
    with app.app_context():
        user = create_user(
            "edit_page_admin",
            "edit_page@example.com",
            role="admin"
        )
        employee_id = create_employee()
        user_id = user.id

    login_as(client, user_id)

    response = client.get(
        f"/admin/employees/{employee_id}/edit"
    )

    assert response.status_code == 200


def test_admin_can_edit_employee(client, app):
    with app.app_context():
        user = create_user(
            "edit_admin",
            "edit_admin@example.com",
            role="admin"
        )
        employee_id = create_employee()
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/employees/{employee_id}/edit",
        data={
            "name": "Петър Петров",
            "position": "Главен механик",
            "phone": "0888999999"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        employee = db.session.get(Employee, employee_id)

        assert employee.name == "Петър Петров"
        assert employee.position == "Главен механик"
        assert employee.phone == "0888999999"


def test_admin_cannot_edit_employee_without_name(client, app):
    with app.app_context():
        user = create_user(
            "invalid_edit_admin",
            "invalid_edit@example.com",
            role="admin"
        )
        employee_id = create_employee()
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/employees/{employee_id}/edit",
        data={
            "name": "",
            "position": "Механик",
            "phone": "0888123456"
        }
    )

    assert response.status_code == 200

    with app.app_context():
        employee = db.session.get(Employee, employee_id)
        assert employee.name == "Иван Петров"


def test_admin_can_deactivate_employee(client, app):
    with app.app_context():
        user = create_user(
            "deactivate_admin",
            "deactivate@example.com",
            role="admin"
        )
        employee_id = create_employee()
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/employees/{employee_id}/toggle"
    )

    assert response.status_code == 302

    with app.app_context():
        employee = db.session.get(Employee, employee_id)
        assert employee.is_active is False


def test_admin_can_activate_employee(client, app):
    with app.app_context():
        user = create_user(
            "activate_admin",
            "activate@example.com",
            role="admin"
        )
        employee_id = create_employee(
            name="Неактивен служител",
            is_active=False
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/employees/{employee_id}/toggle"
    )

    assert response.status_code == 302

    with app.app_context():
        employee = db.session.get(Employee, employee_id)
        assert employee.is_active is True


def test_customer_cannot_add_employee(client, app):
    with app.app_context():
        user = create_user(
            "regular_employee_customer",
            "regular_employee@example.com"
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        "/admin/employees",
        data={
            "name": "Нов служител",
            "position": "Механик",
            "phone": "0888123456"
        }
    )

    assert response.status_code == 403

    with app.app_context():
        assert Employee.query.count() == 0
def test_admin_cannot_add_employee_with_invalid_phone(client, app):
    with app.app_context():
        user = create_user(
            "invalid_phone_admin",
            "invalid_phone@example.com",
            role="admin"
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        "/admin/employees",
        data={
            "name": "Нов служител",
            "position": "Механик",
            "phone": "088812345678"
        }
    )

    assert response.status_code == 200

    with app.app_context():
        assert Employee.query.count() == 0


def test_admin_cannot_add_employee_with_duplicate_phone(client, app):
    with app.app_context():
        user = create_user(
            "duplicate_phone_admin",
            "duplicate_phone@example.com",
            role="admin"
        )
        create_employee()
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        "/admin/employees",
        data={
            "name": "Втори служител",
            "position": "Механик",
            "phone": "+359888123456"
        }
    )

    assert response.status_code == 200

    with app.app_context():
        assert Employee.query.count() == 1


def test_admin_can_add_employee_with_international_phone(client, app):
    with app.app_context():
        user = create_user(
            "international_phone_admin",
            "international_phone@example.com",
            role="admin"
        )
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        "/admin/employees",
        data={
            "name": "Международен номер",
            "position": "Механик",
            "phone": "+359888123456"
        }
    )

    assert response.status_code == 302

    with app.app_context():
        employee = Employee.query.filter_by(
            name="Международен номер"
        ).first()

        assert employee.phone == "0888123456"


def test_admin_can_edit_employee_without_changing_own_phone(client, app):
    with app.app_context():
        user = create_user(
            "same_phone_admin",
            "same_phone@example.com",
            role="admin"
        )
        employee_id = create_employee()
        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/employees/{employee_id}/edit",
        data={
            "name": "Иван Петров",
            "position": "Механик",
            "phone": "0888123456"
        }
    )

    assert response.status_code == 302


def test_admin_cannot_edit_employee_with_another_employee_phone(client, app):
    with app.app_context():
        user = create_user(
            "edit_duplicate_admin",
            "edit_duplicate@example.com",
            role="admin"
        )

        employee_id = create_employee()

        second_employee = Employee(
            name="Втори служител",
            position="Механик",
            phone="0877123456",
            is_active=True
        )
        db.session.add(second_employee)
        db.session.commit()

        user_id = user.id

    login_as(client, user_id)

    response = client.post(
        f"/admin/employees/{employee_id}/edit",
        data={
            "name": "Иван Петров",
            "position": "Механик",
            "phone": "0877123456"
        }
    )

    assert response.status_code == 200

    with app.app_context():
        employee = db.session.get(Employee, employee_id)
        assert employee.phone == "0888123456"