import pytest
from decimal import Decimal
from app.models.referral import Referral
from app.models.client import Client
from app.enums import ClientType, ReferralStatus

def test_referral_creation(db_session):
    """Test Referral model linking two clients."""
    referrer = Client(
        first_name="Referrer",
        last_name="User",
        email="referrer@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    referee = Client(
        first_name="Referee",
        last_name="User",
        email="referee@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add_all([referrer, referee])
    db_session.flush()

    referral = Referral(
        referrer_id=referrer.id,
        referee_id=referee.id,
        status=ReferralStatus.PENDING,
        credit_usd=Decimal("10.00")
    )
    db_session.add(referral)
    db_session.commit()

    assert referral.id is not None
    assert referral.status == ReferralStatus.PENDING
    assert referral.credit_usd == Decimal("10.00")
