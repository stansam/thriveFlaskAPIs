import pytest
from app.repository.client import ClientRepository
from tests.conftest import ClientFactory
from app.models import ClientPreference
from app.enums import ClientType

@pytest.fixture
def repo():
    return ClientRepository()

@pytest.mark.integration
class TestClientRepository:
    def test_find_by_email(self, repo, db_session):
        client = ClientFactory.create(email="test_client@a.com")
        assert repo.find_by_email("test_client@a.com") == client
        assert repo.find_by_email("unknown@a.com") is None

    def test_find_by_whatsapp(self, repo, db_session):
        client = ClientFactory.create(whatsapp_number="+999888777")
        assert repo.find_by_whatsapp("+999888777") == client
        assert repo.find_by_whatsapp("+000") is None

    def test_find_by_passport(self, repo, db_session):
        client = ClientFactory.create(passport_number="AB123456")
        assert repo.find_by_passport("AB123456") == client
        assert repo.find_by_passport("NOPE") is None

    def test_find_referrals_made(self, repo, db_session):
        referrer = ClientFactory.create()
        ref1 = ClientFactory.create(referred_by_id=str(referrer.id))
        ref2 = ClientFactory.create(referred_by_id=str(referrer.id))
        other = ClientFactory.create()

        refs = repo.find_referrals_made(str(referrer.id))
        assert len(refs) == 2
        assert ref1 in refs and ref2 in refs
        assert other not in refs

    def test_find_by_corporate_account(self, repo, db_session):
        c1 = ClientFactory.create(corporate_account_id="corp-1")
        c2 = ClientFactory.create(corporate_account_id="corp-1")
        c3 = ClientFactory.create(corporate_account_id="corp-2")

        corp1_clients = repo.find_by_corporate_account("corp-1")
        assert len(corp1_clients) == 2
        assert c1 in corp1_clients

    def test_marketing_opt_in_list(self, repo, db_session):
        c_opted = ClientFactory.create(is_active=True)
        c_not_opted = ClientFactory.create(is_active=True)
        c_inactive = ClientFactory.create(is_active=False)

        pref1 = ClientPreference(client_id=str(c_opted.id), marketing_opt_in=True, preferred_currency_display="USD")
        pref2 = ClientPreference(client_id=str(c_not_opted.id), marketing_opt_in=False, preferred_currency_display="USD")
        pref3 = ClientPreference(client_id=str(c_inactive.id), marketing_opt_in=True, preferred_currency_display="USD")
        
        db_session.add_all([pref1, pref2, pref3])
        db_session.flush()

        opt_ins = repo.marketing_opt_in_list()
        assert c_opted in opt_ins
        assert c_not_opted not in opt_ins
        assert c_inactive not in opt_ins

    def test_paginate_clients(self, repo, db_session):
        c1 = ClientFactory.create(client_type=ClientType.INDIVIDUAL, is_active=True, first_name="Zack")
        c2 = ClientFactory.create(client_type=ClientType.CORPORATE, is_active=False, first_name="Annie")

        page = repo.paginate_clients()
        assert page.total >= 2

        active_page = repo.paginate_clients(is_active=True)
        assert c1 in active_page.items
        assert c2 not in active_page.items

        corp_page = repo.paginate_clients(client_type=ClientType.CORPORATE)
        assert c2 in corp_page.items

        search_page = repo.paginate_clients(search="Zack")
        assert len(search_page.items) == 1
        assert search_page.items[0] == c1
