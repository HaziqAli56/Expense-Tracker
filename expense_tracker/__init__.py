"""
expense_tracker package — yahan poora Flask backend (Controller + Model wiring) hai.

MVC short map:
- Model:    expense_tracker/models/ (SQLAlchemy tables = SQLite tables)
- View:     expense_tracker/templates/ (HTML5 + Jinja2)
- Controller: expense_tracker/routes/ (URLs, form handling, redirects)
"""

from __future__ import annotations

import os

from flask import Flask

from expense_tracker.config import Config, INSTANCE_DIR
from expense_tracker.extensions import db, login_manager
from expense_tracker.models.transaction_model import Transaction  # noqa: F401 — DB metadata
from expense_tracker.models.user_model import User


def create_app() -> Flask:
    """
    Application factory pattern: Flask app object yahan ban kar return hota hai.

    Faida: tests / alag config ke liye multiple app instances banana asaan ho jata hai.
    """
    # template_folder / static_folder package folder (expense_tracker/) ke relative hain
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # SQLite file ke liye folder (project_root/instance/)
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    # Flask-SQLAlchemy: app se bind
    db.init_app(app)
    # Flask-Login: session-based login
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        """
        Har request par login user ko DB se load karta hai.
        user_id string aata hai (Flask-Login convention); int mein convert karke lookup.
        """
        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            return None
        return db.session.get(User, uid)

    # Blueprints = routes ko modules mein todne ka tareeqa (Controller files)
    from expense_tracker.routes.auth_routes import auth_bp
    from expense_tracker.routes.dashboard_routes import dashboard_bp
    from expense_tracker.routes.transaction_routes import transaction_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transaction_bp)

    # Pehli dafa tables create (agar SQLite file nayi ho)
    with app.app_context():
        db.create_all()

    return app
