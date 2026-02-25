from typing import List, Optional
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, EntityType
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.audit_log.utils import sanitize_audit_payload

class AuditLogRepository(BaseRepository[AuditLog]):
    """
    AuditLogRepository managing append-only operational and security audit trails.
    """

    def __init__(self):
        super().__init__(AuditLog)

    @handle_db_exceptions
    def log_action(
        self, 
        user_id: str, 
        action: AuditAction, 
        entity_type: EntityType, 
        entity_id: str, 
        changes: dict, 
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Inserts an immutable security trail summarizing state mutations securely.
        Aggressively scrubs Personal Identifiable Information (PII) before storage.
        """
        safe_changes = sanitize_audit_payload(changes)
        
        data = {
            'user_id': user_id,
            'action': action,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'changes': safe_changes,
            'ip_address': ip_address
        }
        # Commit True ensures audit trails survive downstream transaction rollbacks elsewhere natively
        return super().create(data, commit=True)

    @handle_db_exceptions
    def get_entity_history(self, entity_type: EntityType, entity_id: str) -> List[AuditLog]:
        """Fetches the chronological mutations of an overarching database record."""
        return self.model.query.filter_by(
            entity_type=entity_type, 
            entity_id=entity_id
        ).order_by(self.model.created_at.desc()).all()

    @handle_db_exceptions
    def get_recent_admin_actions(self, limit: int = 50) -> List[AuditLog]:
        """
        Retrieves recent system-wide actions taken strictly by staff or admins 
        modifying the system externally (e.g. Updating Fee Rules, Modifying Users).
        """
        # Excludes standard actions like LOGIN or regular BOOKING creation for broad reporting
        restricted_actions = [AuditAction.UPDATE, AuditAction.DELETE]
        return self.model.query.filter(
            self.model.action.in_(restricted_actions)
        ).order_by(self.model.created_at.desc()).limit(limit).all()
