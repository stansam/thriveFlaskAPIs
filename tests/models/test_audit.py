import pytest
from app.models.audit import AuditLog
from app.enums import AuditActionType

def test_audit_log_creation(db_session):
    """Test basic AuditLog model creation and defaults."""
    log = AuditLog(
        action=AuditActionType.LOGIN,
        entity_type="user",
        entity_id="user-123",
        description="User logged in",
        ip_address="127.0.0.1"
    )
    db_session.add(log)
    db_session.flush()

    assert log.id is not None
    assert log.action == AuditActionType.LOGIN
    assert log.entity_type == "user"
    assert log.ip_address == "127.0.0.1"
    assert log.created_at is not None
