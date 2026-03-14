import os
from dotenv import load_dotenv

# Load environment variables from .env during local development.
load_dotenv()


def int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


class Config:
    # Flask session/signing key.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    # Optional full DB URL (useful for Docker/hosting platforms).
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        # Prefer a single connection string when it is provided.
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Fallback to individual DB environment variables.
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = os.getenv("DB_PORT", "3306")
        DB_NAME = os.getenv("DB_NAME", "campus_lite")
        DB_USER = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "")

        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    # Disable object change tracking overhead in SQLAlchemy.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Bearer token lifetime for /api authentication, default: 12 hours.
    API_TOKEN_MAX_AGE = int_env("API_TOKEN_MAX_AGE", 43200)
