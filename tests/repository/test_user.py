import pytest
from app.repository.user import UserRepository
from app.enums import UserRole
from tests.conftest import UserFactory


@pytest.fixture
def repo():
    return UserRepository()


@pytest.mark.integration
class TestUserRepository:

    def test_inherited_get(self, repo, db_session):
        user = UserFactory.create()
        fetched = repo.get(str(user.id))
        assert fetched is not None
        assert fetched.id == user.id

    def test_inherited_save(self, repo, db_session):
        user = UserFactory.create(full_name="Old Name")
        user.full_name = "New Name"
        
        saved = repo.save(user, actor_id="test-actor")
        db_session.flush()
        
        assert saved.full_name == "New Name"
        assert saved.updated_by_id == "test-actor"

    def test_inherited_delete(self, repo, db_session):
        user = UserFactory.create()
        uid = str(user.id)
        assert repo.get(uid) is not None
        
        repo.delete(user)
        db_session.flush()
        assert repo.get(uid) is None

    def test_find_by_email(self, repo, db_session):
        user = UserFactory.create(email="test@example.com")
        
        assert repo.find_by_email("test@example.com") == user
        assert repo.find_by_email(" TEST@example.com ") == user  # test normalization
        assert repo.find_by_email("unknown@example.com") is None

    def test_find_active_by_role(self, repo, db_session):
        u1 = UserFactory.create(role=UserRole.AGENT, is_active=True, full_name="A User")
        u2 = UserFactory.create(role=UserRole.SUPER_ADMIN, is_active=True, full_name="B Admin")
        u3 = UserFactory.create(role=UserRole.AGENT, is_active=False, full_name="C Inactive")
        
        agents = repo.find_active_by_role(UserRole.AGENT)
        
        # Only u1 matches exactly (active and agent)
        assert u1 in agents
        assert u2 not in agents
        assert u3 not in agents

    def test_find_all_active(self, repo, db_session):
        active_user = UserFactory.create(is_active=True)
        inactive_user = UserFactory.create(is_active=False)
        
        active_users = repo.find_all_active()
        assert active_user in active_users
        assert inactive_user not in active_users

    def test_deactivate(self, repo, db_session):
        user = UserFactory.create(is_active=True)
        assert user.is_active is True
        
        repo.deactivate(user, actor_id="admin-actor")
        db_session.flush()
        
        fetched = repo.get(str(user.id))
        assert fetched.is_active is False
        assert fetched.updated_by_id == "admin-actor"

    def test_paginate_users(self, repo, db_session):
        # Create users for pagination
        u_agent1 = UserFactory.create(role=UserRole.AGENT, is_active=True, full_name="John Doe", email="jd@a.com")
        u_agent2 = UserFactory.create(role=UserRole.AGENT, is_active=False, full_name="Jane Smith", email="js@a.com")
        u_admin = UserFactory.create(role=UserRole.SUPER_ADMIN, is_active=True, full_name="Test Admin", email="ta@a.com")
        
        # Test basic pagination
        page = repo.paginate_users(per_page=10)
        assert page.total >= 3
        
        # Test filter by role
        agent_page = repo.paginate_users(role=UserRole.AGENT, per_page=10)
        assert u_agent1 in agent_page.items
        assert u_agent2 in agent_page.items
        assert u_admin not in agent_page.items
        
        # Test filter by active status
        active_page = repo.paginate_users(is_active=True, per_page=10)
        assert u_agent1 in active_page.items
        assert u_admin in active_page.items
        assert u_agent2 not in active_page.items
        
        # Test search filter (name)
        search_page = repo.paginate_users(search="jane", per_page=10)
        assert len(search_page.items) == 1
        assert search_page.items[0] == u_agent2
        
        # Test search filter (email)
        search_page2 = repo.paginate_users(search="ta@a.com", per_page=10)
        assert len(search_page2.items) == 1
        assert search_page2.items[0] == u_admin
