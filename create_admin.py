
from getpass import getpass

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():

    print("=== Създаване на администратор ===")

    username = input("Потребителско име: ").strip()
    email = input("Имейл: ").strip().lower()
    password = getpass("Парола: ")

    existing_user = User.query.filter(
        (User.username == username) |
        (User.email == email)
    ).first()

    if existing_user:
        print("Потребител с това име или имейл вече съществува.")

    elif not username or not email or len(password) < 8:
        print("Попълнете всички полета. Паролата трябва да е поне 8 символа.")

    else:
        admin_user = User(
            username=username,
            email=email,
            role="admin"
        )

        admin_user.set_password(password)

        db.session.add(admin_user)
        db.session.commit()

        print("Администраторът е създаден успешно!")
