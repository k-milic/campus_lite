from flask import Blueprint

# Admin blueprint; all admin URLs start with /admin.
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Import routes after blueprint creation to avoid circular imports.
from app.admin import routes
