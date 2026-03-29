import pytest
from decimal import Decimal
from app.repository.loyalty import LoyaltyLedgerRepository
from tests.conftest import ClientFactory
from app.enums import LoyaltyTransactionType

@pytest.fixture
def repo():
    return LoyaltyLedgerRepository()

@pytest.mark.integration
class TestLoyaltyLedgerRepository:
    def test_credit_and_balance(self, repo, db_session):
        client = ClientFactory.create()
        cid = str(client.id)

        assert repo.balance_for_client(cid) == Decimal("0.00")

        repo.credit(cid, Decimal("100.50"), LoyaltyTransactionType.MANUAL_CREDIT, "Reward 1")
        db_session.flush()

        assert repo.balance_for_client(cid) == Decimal("100.50")

        repo.credit(cid, Decimal("50.00"), LoyaltyTransactionType.REFERRAL_CREDIT, "Reward 2")
        db_session.flush()

        assert repo.balance_for_client(cid) == Decimal("150.50")

        records = repo.find_by_client(cid)
        assert len(records) == 2

    def test_redeem(self, repo, db_session):
        client = ClientFactory.create()
        cid = str(client.id)

        repo.credit(cid, Decimal("100.00"), LoyaltyTransactionType.MANUAL_CREDIT, "Initial")
        db_session.flush()

        repo.redeem(cid, Decimal("25.00"), "booking-123")
        db_session.flush()

        assert repo.balance_for_client(cid) == Decimal("75.00")
        
        # Test redeeming more
        repo.redeem(cid, Decimal("75.00"), "booking-124")
        db_session.flush()
        
        assert repo.balance_for_client(cid) == Decimal("0.00")

