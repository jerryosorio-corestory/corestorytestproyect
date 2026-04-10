"""
Application factory for the Library Management System.

Using the factory pattern allows multiple instances of the app to coexist,
which is especially useful for testing (each test gets a fresh instance).
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from config import config_map

# Initialise extensions without binding them to an app yet (deferred binding)
db = SQLAlchemy()
ma = Marshmallow()


def create_app(config_name: str = "default") -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'testing', 'production', or 'default'.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration from the config map
    app.config.from_object(config_map[config_name])

    # Bind extensions to this app instance
    db.init_app(app)
    ma.init_app(app)

    # Register API blueprints (each blueprint owns a resource group)
    from app.routes.books import books_bp
    from app.routes.members import members_bp
    from app.routes.loans import loans_bp

    app.register_blueprint(books_bp, url_prefix="/api/books")
    app.register_blueprint(members_bp, url_prefix="/api/members")
    app.register_blueprint(loans_bp, url_prefix="/api/loans")

    # Create all database tables on first startup
    with app.app_context():
        db.create_all()

    return app
