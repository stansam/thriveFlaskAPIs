import pytest
from app.repository.preference import UserPreferenceRepository, ClientPreferenceRepository
from app.models import UserPreference, ClientPreference
from app.enums import PreferredChannel
from tests.conftest import UserFactory, ClientFactory

@pytest.fixture
def u_repo():
    return UserPreferenceRepository()

@pytest.fixture
def c_repo():
    return ClientPreferenceRepository()

@pytest.mark.integration
class TestPreferenceRepositories:
    def test_user_preferences(self, u_repo, db_session):
        u = UserFactory.create()
        uid = str(u.id)

        assert u_repo.find_by_user(uid) is None

        pref = u_repo.get_or_create(uid)
        db_session.flush()

        assert pref.user_id == uid
        assert u_repo.find_by_user(uid) == pref
        
        pref2 = u_repo.get_or_create(uid)
        assert pref.id == pref2.id

    def test_client_preferences(self, c_repo, db_session):
        c = ClientFactory.create()
        cid = str(c.id)

        pref = c_repo.get_or_create(cid)
        db_session.flush()

        assert pref.client_id == cid
        assert c_repo.find_by_client(cid) == pref

        pref.preferred_channel = PreferredChannel.WHATSAPP
        pref.marketing_opt_in = True
        db_session.flush()

        opted_in = c_repo.find_whatsapp_opted_in()
        assert pref in opted_in
