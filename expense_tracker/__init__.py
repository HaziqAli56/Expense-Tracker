"""
expense_tracker package — Flask app factory
"""

from __future__ import annotations

import os

from flask import Flask

from expense_tracker.config import Config, INSTANCE_DIR
from expense_tracker.extensions import db, login_manager

from expense_tracker.models.user_model import User
from expense_tracker.models.transaction_model import Transaction  # noqa: F401
from expense_tracker.models.budget_model import Budget  # noqa: F401


def create_app() -> Flask:

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    app.config.from_object(Config)

    # ==========================================
    # INSTANCE FOLDER
    # ==========================================

    os.makedirs(
        INSTANCE_DIR,
        exist_ok=True
    )

    # ==========================================
    # EXTENSIONS
    # ==========================================

    db.init_app(app)

    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    # ==========================================
    # USER LOADER
    # ==========================================

    @login_manager.user_loader
    def load_user(user_id: str):

        try:

            return db.session.get(
                User,
                int(user_id)
            )

        except (ValueError, TypeError):

            return None

    # ==========================================
    # BLUEPRINTS
    # ==========================================

    from expense_tracker.routes.auth_routes import auth_bp

    from expense_tracker.routes.dashboard_routes import dashboard_bp

    from expense_tracker.routes.transaction_routes import transaction_bp

    from expense_tracker.routes.report_routes import report_bp

    app.register_blueprint(auth_bp)

    app.register_blueprint(dashboard_bp)

    app.register_blueprint(transaction_bp)

    app.register_blueprint(report_bp)

    # ==========================================
    # CREATE DATABASE TABLES
    # ==========================================

    with app.app_context():

        db.create_all()

    return app