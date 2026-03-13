from flask import Blueprint

# Teacher blueprint; all teacher URLs start with /teacher.
teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

# Import routes after blueprint creation to avoid circular imports.
from app.teacher import routes
