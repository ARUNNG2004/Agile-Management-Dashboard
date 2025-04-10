import pytest
from app import create_app, db
@pytest.fixture()
def app():
    # Create the app with TestConfig
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": 'sqlite:///:memory:',
        "SECRET_KEY": 'test-secret-key',
        "SESSION_PERMANENT": False,
        "SESSION_TYPE": 'filesystem'
    })
    print("Database URI during testing:", app.config['SQLALCHEMY_DATABASE_URI'])
    with app.app_context():
        db.create_all()  # Create database tables
    yield app  # Provide the app to the test

@pytest.fixture()
def client(app):
    # Create a test client for making requests
    return app.test_client()
