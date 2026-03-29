import pytest
from datetime import date
from app.models.fee_schedule import ServiceFeeSchedule

def test_service_fee_schedule_creation(db_session):
    """Test ServiceFeeSchedule model creation."""
    schedule = ServiceFeeSchedule(
        name="2024 Standard",
        effective_from=date(2024, 1, 1),
        is_active=True
    )
    db_session.add(schedule)
    db_session.flush()

    assert schedule.id is not None
    assert schedule.name == "2024 Standard"
    assert schedule.is_active is True
