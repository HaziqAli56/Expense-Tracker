"""
Flask application factory.

The factory pattern keeps configuration, extension setup, and blueprint
registration centralized while allowing tests and deployments to create app
instances predictably.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv  # <-- .env file load karne ke liye

from flask import Flask

# Sabse pehle environment variables load karenge
load_dotenv()

from expense_tracker.config import Config, INSTANCE_DIR
from expense_tracker.extensions import db, login_manager, mail, migrate
from expense_tracker.models.budget_model import Budget  # noqa: F401
from expense_tracker.models.transaction_model import Transaction  # noqa: F401
from expense_tracker.models.user_model import User


def create_app() -> Flask:
    """
    Create, configure, and return the Flask application instance.
    """

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Load database, secret, session, and mail settings from the Config object.
    app.config.from_object(Config)

    # Email Settings ko .env se force read karwaya taake error khatam ho
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Set Currency API configuration from Environment Variables
    app.config["EXCHANGE_RATE_API_KEY"] = os.getenv("EXCHANGE_RATE_API_KEY")
    app.config["EXCHANGE_RATE_API_BASE"] = "https://v6.exchangerate-api.com/v6"

    # Ensure the local fallback database directory exists for development.
    os.makedirs(
        INSTANCE_DIR,
        exist_ok=True,
    )

    # Initialize shared extensions against this concrete Flask app instance.
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Protected routes redirect anonymous visitors to the login screen.
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id: str):
        """
        Load a user from the session-stored id for Flask-Login.
        """
        try:
            return db.session.get(
                User,
                int(user_id),
            )
        except (ValueError, TypeError):
            return None

    # Import blueprints inside the factory to avoid circular import problems.
    from expense_tracker.api.budget_alert_routes import budget_alert_api_bp
    from expense_tracker.api.currency_routes import currency_api_bp
    from expense_tracker.api.forecast_routes import forecast_api_bp
    from expense_tracker.api.import_export_routes import data_api_bp
    from expense_tracker.api.receipt_routes import receipt_api_bp
    from expense_tracker.routes.auth import auth_bp
    from expense_tracker.routes.budget_routes import budget_bp
    from expense_tracker.routes.dashboard_routes import dashboard_bp
    from expense_tracker.routes.report_routes import report_bp
    from expense_tracker.routes.transaction_routes import transaction_api_bp, transaction_bp
    
    # NEW CHATBOT BLUEPRINT IMPORT
    from expense_tracker.routes.chatbot_routes import chatbot_bp

    # Register each feature blueprint with the application router.
    app.register_blueprint(auth_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(transaction_api_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(forecast_api_bp)
    app.register_blueprint(receipt_api_bp)
    app.register_blueprint(data_api_bp)
    app.register_blueprint(currency_api_bp)
    app.register_blueprint(budget_alert_api_bp)
    
    # NEW CHATBOT BLUEPRINT REGISTER
    app.register_blueprint(chatbot_bp)

    # Automatic table creation is opt-in for legacy local development only.
    if app.config["AUTO_CREATE_TABLES"]:
        with app.app_context():
            db.create_all()

    return app