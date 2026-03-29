import pytest
from app.repository.audit import AuditLogRepository
from app.models import AuditLog
from app.enums import AuditActionType

@pytest.fixture
def repo():
    return AuditLogRepository()

@pytest.mark.integration
class TestAuditLogRepository:
    def test_find_for_entity(self, repo, db_session):
        log1 = AuditLog(entity_type="Booking", entity_id="b-1", action=AuditActionType.CREATE, actor_id="a-1", ip_address="127.0.0.1")
        log2 = AuditLog(entity_type="Booking", entity_id="b-1", action=AuditActionType.UPDATE, actor_id="a-2", ip_address="127.0.0.1")
        log3 = AuditLog(entity_type="User", entity_id="u-1", action=AuditActionType.UPDATE, actor_id="a-2", ip_address="127.0.0.1")
        db_session.add_all([log1, log2, log3])
        db_session.flush()

        page = repo.find_for_entity("Booking", "b-1")
        assert page.total == 2
        
    def test_find_by_actor_and_action(self, repo, db_session):
        log1 = AuditLog(entity_type="X", entity_id="x-1", action=AuditActionType.DELETE, actor_id="agent-99", ip_address="1.2.3.4")
        db_session.add(log1)
        db_session.flush()

        actor_page = repo.find_by_actor("agent-99")
        assert len(actor_page.items) == 1
        assert actor_page.items[0] == log1

        action_list = repo.find_by_action(AuditActionType.DELETE)
        assert log1 in action_list

    def test_immutability(self, repo, db_session):
        log = AuditLog(entity_type="Y", entity_id="y-1", action=AuditActionType.CREATE, actor_id="a-1", ip_address="1.2.3.4")
        repo.save(log)
        db_session.flush()

        with pytest.raises(NotImplementedError):
            repo.update(log, ip_address="new-ip")

        with pytest.raises(NotImplementedError):
            repo.delete(log)
