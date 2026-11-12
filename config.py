import os
from dotenv import load_dotenv

# Зареждане на настройките от .env
load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "development-secret-key-change-me"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///autoservice.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False