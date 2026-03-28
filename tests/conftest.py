import os
import tempfile
import pytest
from app import create_app
from app.models.base import db as _db

@pytest.fixture(scope="function")
def app():
    """Create a Flask app instance for testing with a unique database."""
    db_fd, db_path = tempfile.mkstemp()
    test_config = {
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{db_path}",
        'Testing': True
    }
    app = create_app("testing", test_config=test_config)
    
    yield app
    
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture(scope="function")
def db_session(app):
    """Provide a clean database session for each test."""
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.remove()
        _db.drop_all()

# # tests/conftest.py
# """
# Pytest fixtures for the Thrive Global Travel & Tours test suite.

# Fixture hierarchy
# -----------------
#     app           — Flask application in TESTING mode (session-scoped)
#     db_session    — SQLAlchemy session with rollback after each test
#     client        — Flask test client (function-scoped, rolls back DB)
#     admin_user    — A seeded SUPER_ADMIN User instance
#     agent_user    — A seeded AGENT User instance
#     admin_headers — Authorization headers for the super admin
#     agent_headers — Authorization headers for the agent

# Database isolation strategy
# ---------------------------
# Each test function runs inside a nested SQLAlchemy transaction (SAVEPOINT)
# that is rolled back after the test completes.  This means:
#   - No data leaks between tests
#   - No need to truncate tables between tests
#   - Tests run against a real SQLite schema, not mocks

# Test data factories (factory_boy)
# ----------------------------------
# UserFactory, ClientFactory, BookingFactory are available after import:
#     from tests.conftest import UserFactory
# """

# from __future__ import annotations

# import pytest
# import factory
# from factory.alchemy import SQLAlchemyModelFactory
# from flask import Flask
# from flask.testing import FlaskClient

# from app import create_app
# from models.base import db as _db
# from models.user import User, UserRole
# from models.client import Client, ClientType
# from core.security import hash_password, create_access_token
# from core.config import settings


# # ---------------------------------------------------------------------------
# # Application fixture  (session-scoped — created once per test session)
# # ---------------------------------------------------------------------------

# @pytest.fixture(scope="session")
# def app() -> Flask:
#     """
#     Create a fully configured Flask application in TESTING mode.

#     Uses an in-memory SQLite database so tests are isolated from
#     any development database.
#     """
#     flask_app = create_app(
#         env="testing",
#         test_config={
#             "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
#             "TESTING": True,
#             "WTF_CSRF_ENABLED": False,
#             "RATELIMIT_ENABLED": False,   # disable rate limiting in tests
#         },
#     )
#     yield flask_app


# # ---------------------------------------------------------------------------
# # Database schema fixture  (session-scoped — schema created once)
# # ---------------------------------------------------------------------------

# @pytest.fixture(scope="session")
# def _db_schema(app: Flask):
#     """Create all tables once for the entire test session."""
#     with app.app_context():
#         _db.create_all()
#     yield
#     with app.app_context():
#         _db.drop_all()


# # ---------------------------------------------------------------------------
# # DB session with rollback isolation  (function-scoped)
# # ---------------------------------------------------------------------------

# @pytest.fixture(autouse=True)
# def db_session(app: Flask, _db_schema):
#     """
#     Wrap each test in a SAVEPOINT so all writes are rolled back afterwards.

#     The `autouse=True` means this runs for EVERY test automatically,
#     ensuring database isolation without explicit cleanup.
#     """
#     with app.app_context():
#         connection = _db.engine.connect()
#         transaction = connection.begin()

#         # Bind the session to our connection so it shares the transaction
#         _db.session.bind = connection  # type: ignore[assignment]

#         # Create a SAVEPOINT for nested rollback
#         nested = connection.begin_nested()

#         yield _db.session

#         # Roll back to the SAVEPOINT — wipes all test writes
#         nested.rollback()
#         transaction.rollback()
#         connection.close()
#         _db.session.remove()


# # ---------------------------------------------------------------------------
# # Flask test client  (function-scoped)
# # ---------------------------------------------------------------------------

# @pytest.fixture
# def client(app: Flask, db_session) -> FlaskClient:
#     """Flask test client, database isolated per test."""
#     return app.test_client()


# # ---------------------------------------------------------------------------
# # Seeded users
# # ---------------------------------------------------------------------------

# @pytest.fixture
# def admin_user(db_session) -> User:
#     """A SUPER_ADMIN user persisted in the test DB."""
#     user = User(
#         email="admin@test.thrive.com",
#         full_name="Test Admin",
#         password_hash=hash_password("AdminPass1!"),
#         role=UserRole.SUPER_ADMIN,
#         is_active=True,
#     )
#     db_session.add(user)
#     db_session.flush()
#     return user


# @pytest.fixture
# def agent_user(db_session) -> User:
#     """An AGENT user persisted in the test DB."""
#     user = User(
#         email="agent@test.thrive.com",
#         full_name="Test Agent",
#         password_hash=hash_password("AgentPass1!"),
#         role=UserRole.AGENT,
#         is_active=True,
#     )
#     db_session.add(user)
#     db_session.flush()
#     return user


# @pytest.fixture
# def inactive_user(db_session) -> User:
#     """An inactive user for testing account-inactive paths."""
#     user = User(
#         email="inactive@test.thrive.com",
#         full_name="Inactive User",
#         password_hash=hash_password("InactivePass1!"),
#         role=UserRole.AGENT,
#         is_active=False,
#     )
#     db_session.add(user)
#     db_session.flush()
#     return user


# # ---------------------------------------------------------------------------
# # Auth header helpers
# # ---------------------------------------------------------------------------

# def _auth_headers(user: User) -> dict[str, str]:
#     """Generate a valid JWT Bearer header for a user."""
#     token = create_access_token(user.id, user.role.value)
#     return {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json",
#         "X-Request-ID": "test-request-id",
#     }


# @pytest.fixture
# def admin_headers(admin_user: User) -> dict[str, str]:
#     """Authorization headers for the test super admin."""
#     return _auth_headers(admin_user)


# @pytest.fixture
# def agent_headers(agent_user: User) -> dict[str, str]:
#     """Authorization headers for the test agent."""
#     return _auth_headers(agent_user)


# # ---------------------------------------------------------------------------
# # Factory Boy model factories
# # ---------------------------------------------------------------------------

# class BaseFactory(SQLAlchemyModelFactory):
#     class Meta:
#         abstract = True
#         sqlalchemy_session_persistence = "flush"

#     @classmethod
#     def _get_session(cls):
#         # Resolve session lazily from Flask-SQLAlchemy scoped session
#         return _db.session


# class UserFactory(BaseFactory):
#     class Meta:
#         model = User

#     email        = factory.Sequence(lambda n: f"user{n}@thrive.test")
#     full_name    = factory.Faker("name")
#     password_hash = factory.LazyFunction(lambda: hash_password("TestPass1!"))
#     role         = UserRole.AGENT
#     is_active    = True
#     mfa_secret   = None
#     phone        = factory.Faker("phone_number")


# class ClientFactory(BaseFactory):
#     class Meta:
#         model = Client

#     first_name        = factory.Faker("first_name")
#     last_name         = factory.Faker("last_name")
#     email             = factory.Sequence(lambda n: f"client{n}@thrive.test")
#     phone             = factory.Faker("phone_number")
#     whatsapp_number   = factory.Faker("phone_number")
#     client_type       = ClientType.INDIVIDUAL
#     is_active         = True
#     preferred_language = "en"


# # ---------------------------------------------------------------------------
# # JSON helpers
# # ---------------------------------------------------------------------------

# @pytest.fixture
# def json_headers() -> dict[str, str]:
#     """Unauthenticated JSON request headers."""
#     return {
#         "Content-Type": "application/json",
#         "X-Request-ID": "test-anon-request-id",
#     }