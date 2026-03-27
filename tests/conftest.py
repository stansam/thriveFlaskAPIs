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
