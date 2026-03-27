import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from app.models.corporate import CorporateAccount, CorporateSubscription
from app.enums import SubscriptionTier

def test_corporate_account_and_subscription(db_session):
    """Test CorporateAccount and its linked subscription."""
    account = CorporateAccount(
        company_name="Thrive Corp",
        billing_email="billing@thrivecorp.com"
    )
    db_session.add(account)
    db_session.flush()

    now = datetime.now(timezone.utc)
    subscription = CorporateSubscription(
        account_id=account.id,
        tier=SubscriptionTier.SILVER,
        monthly_fee=Decimal("300.00"),
        bookings_limit=15,
        billing_cycle_start=now,
        billing_cycle_end=now + timedelta(days=30)
    )
    db_session.add(subscription)
    db_session.commit()

    assert account.id is not None
    assert subscription.id is not None
    assert account.subscription.tier == SubscriptionTier.SILVER
    assert subscription.is_at_limit() is False
    
    subscription.bookings_used = 15
    assert subscription.is_at_limit() is True
