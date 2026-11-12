from flask import Blueprint, render_template
from app.models import Service

services = Blueprint("services", __name__, url_prefix="/services")


@services.route("/")
def index():
    all_services = Service.query.filter_by(
        is_active=True
    ).order_by(Service.name).all()

    return render_template(
        "services/index.html",
        services=all_services
    )