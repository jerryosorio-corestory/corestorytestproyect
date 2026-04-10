"""
Pytest fixtures shared across all test modules.

Using the application factory with 'testing' config ensures each test
run gets a fresh in-memory SQLite database, preventing test pollution.
"""

import pytest
from app import create_app, db as _db


@pytest.fixture(scope="session")
def app():
    """Create the Flask app configured for testing (in-memory SQLite)."""
    application = create_app("testing")
    yield application


@pytest.fixture(scope="session")
def client(app):
    """Return a test client that can send HTTP requests to the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def reset_db(app):
    """
    Recreate all tables before every test so each test starts with a clean slate.
    The 'autouse=True' means this fixture runs automatically for every test.
    """
    with app.app_context():
        _db.drop_all()
        _db.create_all()
    yield
    # Teardown: nothing extra needed — next test will reset again
