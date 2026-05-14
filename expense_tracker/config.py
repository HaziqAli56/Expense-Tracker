
"""
Configuration — SECRET_KEY aur DATABASE URL (SQLite path).

Ye file "settings" layer hai: production mein yahan environment variables se
strong SECRET_KEY aur alag DB URL diye jate hain.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

# .env file load karega
load_dotenv()

# Is file ka folder = expense_tracker/
_PKG_DIR = os.path.abspath(os.path.dirname(__file__))

# Project root = ek level upar (jahan run.py / requirements.txt hain)
PROJECT_ROOT = os.path.dirname(_PKG_DIR)

# SQLite file yahan banegi
INSTANCE_DIR = os.path.join(PROJECT_ROOT, "instance")


class Config:
    """
    Flask app configuration
    """

    # Secret key (.env se read hogi)
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "fallback-secret-key"
    )

    # Database URL (.env se read hogi)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(INSTANCE_DIR, "expenses.db")
    )

    # Performance optimization
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Extra security
    SESSION_COOKIE_HTTPONLY = True

    REMEMBER_COOKIE_HTTPONLY = True
