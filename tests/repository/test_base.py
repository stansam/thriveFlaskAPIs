import pytest
from sqlalchemy import select
from werkzeug.exceptions import NotFound

from app.repository.user import UserRepository
from app.models import User
from tests.conftest import UserFactory


@pytest.fixture
def repo():
    return UserRepository()


@pytest.mark.integration
class TestBaseRepository:
    """
    Test the BaseRepository methods by using UserRepository 
    as the concrete implementation.
    """

    def test_get(self, repo, db_session):
        user = UserFactory.create()
        fetched = repo.get(str(user.id))
        assert fetched is not None
        assert fetched.id == user.id

    def test_get_not_found(self, repo, db_session):
        import uuid
        assert repo.get(str(uuid.uuid4())) is None

    def test_get_or_404(self, repo, db_session):
        user = UserFactory.create()
        fetched = repo.get_or_404(str(user.id))
        assert fetched.id == user.id

        import uuid
        with pytest.raises(NotFound):
            repo.get_or_404(str(uuid.uuid4()))

    def test_get_by(self, repo, db_session):
        user = UserFactory.create(email="unique_by@test.com")
        fetched = repo.get_by(email="unique_by@test.com")
        assert fetched is not None
        assert fetched.id == user.id

    def test_get_by_or_404(self, repo, db_session):
        user = UserFactory.create(email="unique_by404@test.com")
        fetched = repo.get_by_or_404(email="unique_by404@test.com")
        assert fetched.id == user.id

        with pytest.raises(NotFound):
            repo.get_by_or_404(email="missing@test.com")

    def test_all_and_list_by(self, repo, db_session):
        u1 = UserFactory.create(full_name="Alpha")
        u2 = UserFactory.create(full_name="Beta")
        UserFactory.create(full_name="Gamma") # u3
        
        all_users = repo.all()
        assert len(all_users) >= 3

        matches = repo.list_by(full_name="Alpha")
        assert len(matches) == 1
        assert matches[0].id == u1.id

    def test_paginate(self, repo, db_session):
        UserFactory.create_batch(5, full_name="Paginate User")
        
        stmt = select(User).where(User.full_name == "Paginate User")
        
        page = repo.paginate(stmt, page=1, per_page=2)
        assert page.total == 5
        assert page.page == 1
        assert page.per_page == 2
        assert page.total_pages == 3
        assert page.has_next is True
        assert page.has_prev is False
        assert len(page.items) == 2

    def test_exists_and_count(self, repo, db_session):
        user = UserFactory.create(email="count_exists@test.com")
        
        assert repo.exists(email="count_exists@test.com") is True
        assert repo.exists(email="no_such_user@test.com") is False
        
        stmt = select(User).where(User.email == "count_exists@test.com")
        assert repo.count(stmt) == 1

    def test_create(self, repo, db_session):
        user = repo.create(
            actor_id="admin123",
            email="created@test.com",
            full_name="Created User",
            password_hash="pwd",
            is_active=True
        )
        assert user.id is not None
        assert user.created_by_id == "admin123"

    def test_update(self, repo, db_session):
        user = UserFactory.create(full_name="Before")
        updated = repo.update(user, actor_id="admin123", full_name="After")
        
        assert updated.full_name == "After"
        assert updated.updated_by_id == "admin123"

    def test_delete_by_id(self, repo, db_session):
        user = UserFactory.create()
        uid = str(user.id)
        
        assert repo.delete_by_id(uid) is True
        assert repo.get(uid) is None
        assert repo.delete_by_id(uid) is False

    def test_bulk_create_and_update(self, repo, db_session):
        items = [
            {"email": "bulk1@test.com", "full_name": "B1", "password_hash": "pwd", "is_active": True},
            {"email": "bulk2@test.com", "full_name": "B2", "password_hash": "pwd", "is_active": True}
        ]
        
        created = repo.bulk_create(items, actor_id="bulk-admin")
        assert len(created) == 2
        
        created[0].full_name = "B1 Changed"
        created[1].full_name = "B2 Changed"
        
        updated = repo.bulk_update(created, actor_id="bulk-updater")
        assert updated[0].full_name == "B1 Changed"
        assert updated[0].updated_by_id == "bulk-updater"
