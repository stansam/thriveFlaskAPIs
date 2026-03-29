import pytest
from datetime import datetime
from app.repository.corporate import CorporateAccountRepository, CorporateSubscriptionRepository
from app.models import CorporateAccount, CorporateSubscription
from app.enums import SubscriptionTier

@pytest.fixture
def account_repo():
    return CorporateAccountRepository()

@pytest.fixture
def sub_repo():
    return CorporateSubscriptionRepository()

@pytest.mark.integration
class TestCorporateAccountRepository:
    def test_find_by_company_name(self, account_repo, db_session):
        c1 = CorporateAccount(company_name="Acme Corp", billing_email="1@c.com", is_active=True)
        db_session.add(c1)
        db_session.flush()

        results = account_repo.find_by_company_name("Acme")
        assert len(results) == 1
        assert results[0] == c1

    def test_find_active(self, account_repo, db_session):
        c1 = CorporateAccount(company_name="Active Corp", billing_email="2@c.com", is_active=True)
        c2 = CorporateAccount(company_name="Inactive Corp", billing_email="3@c.com", is_active=False)
        db_session.add_all([c1, c2])
        db_session.flush()

        active = account_repo.find_active()
        assert c1 in active
        assert c2 not in active

    def test_paginate_accounts(self, account_repo, db_session):
        c1 = CorporateAccount(company_name="Find Me Now", billing_email="4@c.com", is_active=True)
        c2 = CorporateAccount(company_name="Hide Me Later", billing_email="5@c.com", is_active=False)
        db_session.add_all([c1, c2])
        db_session.flush()

        page = account_repo.paginate_accounts(search="Find Me")
        assert len(page.items) == 1
        assert page.items[0] == c1

        page2 = account_repo.paginate_accounts(is_active=False)
        assert c2 in page2.items
        assert c1 not in page2.items

@pytest.mark.integration
class TestCorporateSubscriptionRepository:
    def test_find_by_account_and_tier(self, sub_repo, db_session):
        account = CorporateAccount(company_name="Sub Corp", billing_email="6@c.com", is_active=True)
        db_session.add(account)
        db_session.flush()

        sub = CorporateSubscription(
            account_id=str(account.id),
            tier=SubscriptionTier.GOLD,
            monthly_fee=100.0,
            is_active=True,
            billing_cycle_start=datetime.now(),
            billing_cycle_end=datetime.now(),
            bookings_used=0
        )
        db_session.add(sub)
        db_session.flush()

        found = sub_repo.find_by_account(str(account.id))
        assert found == sub

        ent_active = sub_repo.find_active_by_tier(SubscriptionTier.GOLD)
        assert sub in ent_active

    def test_increment_and_reset(self, sub_repo, db_session):
        account = CorporateAccount(company_name="Inc Corp", billing_email="7@c.com", is_active=True)
        db_session.add(account)
        db_session.flush()

        sub = CorporateSubscription(
            account_id=str(account.id),
            tier=SubscriptionTier.GOLD,
            monthly_fee=100.0,
            is_active=True,
            billing_cycle_start=datetime.now(),
            billing_cycle_end=datetime.now(),
            bookings_used=5
        )
        db_session.add(sub)
        db_session.flush()

        updated = sub_repo.increment_bookings_used(sub, actor_id="sys")
        assert updated.bookings_used == 6

        now = datetime.now()
        later = datetime.now()
        reset_sub = sub_repo.reset_billing_cycle(sub, now, later, actor_id="sys")
        assert reset_sub.bookings_used == 0
        assert reset_sub.billing_cycle_start == now
        assert reset_sub.billing_cycle_end == later
