from flask import Blueprint

# JSON REST API blueprint.
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Import routes after blueprint creation to avoid circular imports.
from app.api import routes
