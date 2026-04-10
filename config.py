"""
Application configuration settings.
Defines separate configurations for development, testing, and production environments.
"""

import os


class Config:
    """Base configuration shared by all environments."""

    # Secret key used for session signing and CSRF protection
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # SQLAlchemy settings — disable modification tracking to save memory
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Business rules — centralised so they can be changed in one place
    MAX_LOANS_PER_MEMBER = 3          # Maximum books a member can borrow at once
    LOAN_PERIOD_DAYS = 14             # Standard loan period in days
    LATE_FEE_PER_DAY = 0.50          # Late fee charged per overdue day (USD)
    MAX_LATE_FEE = 10.00             # Cap on total late fee per loan (USD)


class DevelopmentConfig(Config):
    """Development configuration — uses a local SQLite file."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///library_dev.db"
    )


class TestingConfig(Config):
    """Testing configuration — uses an in-memory SQLite database."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Disable CSRF protection in tests
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration — expects a proper DATABASE_URL env variable."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///library.db")


# Map string names to config classes for easy lookup
config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
