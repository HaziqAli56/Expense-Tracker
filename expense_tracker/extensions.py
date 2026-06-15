"""
Shared Flask extension instances.

Extensions are created once here and initialized inside the app factory. This
avoids circular imports and keeps models, routes, and utilities using the same
database, login, and mail objects.
"""

from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


# SQLAlchemy powers the application models and database sessions.
db = SQLAlchemy()

# Flask-Login owns session loading, login-required redirects, and current_user.
login_manager = LoginManager()

# Guests who access protected routes are redirected to the login endpoint.
login_manager.login_view = "auth.login"

# Flash category used when Flask-Login redirects unauthenticated visitors.
login_manager.login_message_category = "info"

# Flask-Mail sends forgot-password reset emails through configured SMTP.
mail = Mail()

# Flask-Migrate/Alembic manages production-safe database schema migrations.
migrate = Migrate()
