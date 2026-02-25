from dataclasses import dataclass
from typing import Optional, Dict, Any
from app.models.enums import AuditAction, EntityType

@dataclass
class LogActionDTO:
    action: AuditAction
    user_id: Optional[str] = None
    entity_type: Optional[EntityType] = None
    entity_id: Optional[str] = None
    description: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
