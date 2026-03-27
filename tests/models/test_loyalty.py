import pytest
from decimal import Decimal
from app.models.loyalty import LoyaltyLedger
from app.models.client import Client
from app.enums import ClientType, LoyaltyTransactionType

def test_loyalty_ledger_creation(db_session):
    """Test LoyaltyLedger model creation and signing."""
    client = Client(
        first_name="Loyalty",
        last_name="Member",
        email="loyalty@example.com",
        client_type=ClientType.INDIVIDUAL
    )
    db_session.add(client)
    db_session.flush()

    ledger_entry = LoyaltyLedger(
        client_id=client.id,
        transaction_type=LoyaltyTransactionType.REFERRAL_CREDIT,
        amount_usd=Decimal("10.00"),
        description="Referral reward for inviting Bob"
    )
    db_session.add(ledger_entry)
    db_session.commit()

    assert ledger_entry.id is not None
    assert ledger_entry.amount_usd == Decimal("10.00")
    assert ledger_entry.client.first_name == "Loyalty"
