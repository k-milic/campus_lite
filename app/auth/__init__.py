from flask import Blueprint

# Authentication blueprint (login, register, logout).
auth_bp = Blueprint("auth", __name__)

# Import routes after blueprint creation to avoid circular imports.
from app.auth import routes
