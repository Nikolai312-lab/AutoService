from flask import Flask

from config import Config
from app.extensions import db, migrate, login_manager
from app.routes.auth import auth
from app.routes.main import main
from app.routes.vehicles import vehicles   
from app.routes.services import services
from app.routes.appointments import appointments
from app.routes.admin import admin
from app.routes.reviews import reviews


def create_app(config_class=Config):
    app = Flask(__name__)

    # Зареждане на конфигурацията
    app.config.from_object(config_class)
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(vehicles)
    app.register_blueprint(services)
    app.register_blueprint(appointments)
    app.register_blueprint(admin)
    app.register_blueprint(reviews)
    
    # Инициализиране на разширенията
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Зареждане на моделите
    from app import models
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    return app