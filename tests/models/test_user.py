import pytest
from app.models.user import User
from app.enums import UserRole

def test_user_creation(db_session):
    """Test basic User model creation and defaults."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash="hashed_password",
        role=UserRole.AGENT
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.role == UserRole.AGENT
