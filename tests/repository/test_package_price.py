import pytest
from decimal import Decimal
from app.repository.package_price import PackagePriceTierRepository
from app.models import PackagePriceTier

@pytest.fixture
def repo():
    return PackagePriceTierRepository()

@pytest.mark.integration
class TestPackagePriceTierRepository:
    def test_find_by_package(self, repo, db_session):
        t1 = PackagePriceTier(
            package_id="P1", label="L1", price_usd=Decimal("100"), 
            price_per="person", min_participants=1, max_participants=2,
            is_add_on=False, is_active=True
        )
        t2 = PackagePriceTier(
            package_id="P1", label="L2", price_usd=Decimal("80"), 
            price_per="person", min_participants=3, max_participants=None,
            is_add_on=False, is_active=False
        )
        db_session.add_all([t1, t2])
        db_session.flush()

        active = repo.find_by_package("P1", active_only=True)
        assert len(active) == 1
        assert active[0] == t1

        all_tiers = repo.find_by_package("P1", active_only=False)
        assert len(all_tiers) == 2

    def test_find_matching_tier(self, repo, db_session):
        t1 = PackagePriceTier(
            package_id="P1", label="1-2 Pax", price_usd=Decimal("100"), 
            price_per="person", min_participants=1, max_participants=2,
            is_add_on=False, is_active=True
        )
        t2 = PackagePriceTier(
            package_id="P1", label="3+ Pax", price_usd=Decimal("80"), 
            price_per="person", min_participants=3, max_participants=None,
            is_add_on=False, is_active=True
        )
        db_session.add_all([t1, t2])
        db_session.flush()

        tier_group1 = repo.find_matching_tier("P1", num_participants=2, is_add_on=False)
        assert tier_group1 == t1

        tier_group2 = repo.find_matching_tier("P1", num_participants=5, is_add_on=False)
        assert tier_group2 == t2

        no_match = repo.find_matching_tier("P1", num_participants=2, is_add_on=True)
        assert no_match is None
