from flask import request
from app.repository import repositories
from app.dto.audit.schemas import LogActionDTO
from app.services.audit.utils import construct_change_diff

class AuditService:
    """
    AuditService offers a strict append-only ledger managing explicitly decoupled 
    system event tracking protecting administrative liabilities natively.
    """

    def __init__(self):
        self.audit_repo = repositories.audit_log

    def record_critical_action(self, payload: LogActionDTO) -> None:
        """
        Ingests explicit transactional boundaries (e.g. USER_PROMOTED, BOOKING_REFUNDED)
        isolating them asynchronously securing immutable forensic trails safely.
        """
        
        # Optionally grab physical IP/Agent mappings actively if executed within a live Request Context
        current_ip = payload.ip_address
        current_agent = None
        
        if not current_ip:
             try:
                 current_ip = request.remote_addr
                 current_agent = request.user_agent.string
             except RuntimeError:
                 # Cleanly bypassed out-of-request context failures natively
                 pass

        self.audit_repo.create({
            "user_id": payload.user_id,
            "action": payload.action,
            "entity_type": payload.entity_type,
            "entity_id": payload.entity_id,
            "description": payload.description,
            "changes": payload.changes,
            "ip_address": current_ip,
            "user_agent": current_agent
        }, commit=True)
