from datetime import datetime
from flask import request, has_request_context
from app.extensions import db
from app.models.audit_log import AuditLog
from app.models.enums import AuditAction, EntityType
import logging

logger = logging.getLogger(__name__)

def log_audit(
    action: AuditAction,
    entity_type: EntityType = None,
    entity_id: str = None,
    user_id: str = None,
    changes: dict = None,
    description: str = None
):
    """
    Creates an audit log entry.
    
    Args:
        action (AuditAction): The action performed.
        entity_type (EntityType, optional): The type of entity affected.
        entity_id (str, optional): The ID of the entity affected.
        user_id (str, optional): The ID of the user performing the action.
        changes (dict, optional): A dictionary of changes (old vs new values).
        description (str, optional): A text description of the event.
    """
    try:
        ip_address = None
        user_agent = None
        
        if has_request_context():
            ip_address = request.remote_addr
            user_agent = request.user_agent.string if request.user_agent else None

        audit_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            changes=changes,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(audit_entry)
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        db.session.rollback()
