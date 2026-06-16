"""
Application configuration.

Security-sensitive settings are read from environment variables so production
deployments can provide strong secrets, PostgreSQL URLs, and SMTP credentials
without committing them to source control.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv


# Load local .env values for development without affecting production overrides.
load_dotenv()

# Resolve the package directory so fallback local paths are deterministic.
_PKG_DIR = os.path.abspath(os.path.dirname(__file__))

# Resolve the project root where run.py, requirements.txt, and instance/ live.
PROJECT_ROOT = os.path.dirname(_PKG_DIR)

# SQLite fallback database lives in instance/ when DATABASE_URL is not supplied.
INSTANCE_DIR = os.path.join(PROJECT_ROOT, "instance")


class Config:
    """
    Central Flask configuration object loaded by the app factory.
    """

    # SECRET_KEY signs sessions, CSRF tokens, and password-reset tokens.
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "fallback-secret-key",
    )

    # DATABASE_URL should point to PostgreSQL in production.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(INSTANCE_DIR, "expenses_v2.db"),  # <--- Sirf ye naam change kiya
   )

    # Local-only escape hatch for legacy development databases without migrations.
    AUTO_CREATE_TABLES = os.environ.get("AUTO_CREATE_TABLES", "false").lower() == "true"

    # Disabling modification tracking reduces SQLAlchemy overhead.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # HttpOnly cookies reduce exposure to client-side script access.
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    # Flask-Mail SMTP settings are read from environment variables for safety.
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "25"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        "noreply@expense-tracker.local",
    )

    # Receipt upload limit protects the API from oversized image payloads.
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024)))

    # Receipt scanner accepts common browser/mobile image formats only.
    ALLOWED_RECEIPT_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    ALLOWED_RECEIPT_MIMETYPES = {"image/png", "image/jpeg", "image/webp"}
    TESSERACT_CMD = os.environ.get("TESSERACT_CMD")

    # Bulk imports are intentionally capped so one upload cannot overwhelm the app.
    MAX_IMPORT_ROWS = int(os.environ.get("MAX_IMPORT_ROWS", "5000"))
    ALLOWED_IMPORT_EXTENSIONS = {"csv", "xlsx"}

    # Exchange-rate API settings are configurable so providers can be swapped.
    EXCHANGE_RATE_API_BASE = os.environ.get(
        "EXCHANGE_RATE_API_BASE",
        "https://open.er-api.com/v6/latest",
    )

    # Default dashboard/base currency used when a user preference is not present.
    DEFAULT_BASE_CURRENCY = os.environ.get("DEFAULT_BASE_CURRENCY", "PKR")
