import pytest
from decimal import Decimal
from datetime import date
from app.models.fee import ServiceFee
from app.models.fee_schedule import ServiceFeeSchedule
from app.enums import FeeType

def test_service_fee_creation(db_session):
    """Test ServiceFee model and its relationship to schedule."""
    schedule = ServiceFeeSchedule(
        name="Test Schedule",
        effective_from=date(2024, 1, 1),
        is_active=True
    )
    db_session.add(schedule)
    db_session.flush()

    fee = ServiceFee(
        schedule_id=schedule.id,
        fee_type=FeeType.DOMESTIC_FLIGHT,
        label="Domestic Flight Fee",
        amount_usd=Decimal("25.00"),
        min_amount_usd=Decimal("25.00"),
        max_amount_usd=Decimal("50.00")
    )
    db_session.add(fee)
    db_session.flush()

    assert fee.id is not None
    assert fee.schedule.name == "Test Schedule"
    assert fee.amount_usd == Decimal("25.00")
    assert fee.is_per_passenger is False
