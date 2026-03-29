import pytest
from app.models.user_preference import UserPreference
from app.models.user import User
from app.enums import ThemePreference, DashboardLayout

def test_user_preference_creation(db_session):
    """Test UserPreference 1:1 relationship and defaults."""
    user = User(
        full_name="Admin User",
        email="admin.pref@example.com",
        password_hash="hash"
    )
    db_session.add(user)
    db_session.flush()

    pref = UserPreference(
        user_id=user.id,
        theme=ThemePreference.DARK,
        dashboard_layout=DashboardLayout.BOOKINGS
    )
    db_session.add(pref)
    db_session.flush()

    assert pref.id is not None
    assert pref.user_id == user.id
    assert pref.theme == ThemePreference.DARK
    assert pref.notify_new_booking is True  # Default
    assert pref.items_per_page == 25  # Default
