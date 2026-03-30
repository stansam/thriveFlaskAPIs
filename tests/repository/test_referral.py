import pytest
from decimal import Decimal
from app.repository.referral import ReferralRepository
from app.models import Referral
from app.enums import ReferralStatus
from tests.conftest import ClientFactory

@pytest.fixture
def repo():
    return ReferralRepository()

@pytest.mark.integration
class TestReferralRepository:
    def test_queries(self, repo, db_session):
        c1 = ClientFactory.create()
        c2 = ClientFactory.create()

        r = Referral(
            referrer_id=str(c1.id), referee_id=str(c2.id),
            status=ReferralStatus.PENDING, credit_usd=Decimal("10")
        )
        db_session.add(r)
        db_session.flush()

        by_referrer = repo.find_by_referrer(str(c1.id))
        assert len(by_referrer) == 1

        assert repo.find_by_referee(str(c2.id)) == r

        pending = repo.find_pending()
        assert r in pending

    def test_mutations(self, repo, db_session):
        c1 = ClientFactory.create()
        c2 = ClientFactory.create()

        r = Referral(
            referrer_id=str(c1.id), referee_id=str(c2.id),
            status=ReferralStatus.PENDING, credit_usd=Decimal("10")
        )
        db_session.add(r)
        db_session.flush()

        repo.qualify(r, "B1")
        assert r.status == ReferralStatus.QUALIFIED
        assert r.qualifying_booking_id == "B1"

        repo.credit(r)
        assert r.status == ReferralStatus.CREDITED
