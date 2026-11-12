from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# База данни
db = SQLAlchemy()

# Миграции на базата данни
migrate = Migrate()

# Управление на потребителските сесии
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Моля, влезте в профила си."
login_manager.login_message_category = "warning"