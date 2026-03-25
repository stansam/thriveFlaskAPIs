# dtos/audit.py
from __future__ import annotations
from app.enums import AuditActionType
from .common import AuditFieldsMixin


class AuditLogResponse(AuditFieldsMixin):
    actor_id: str | None
    action: AuditActionType
    entity_type: str
    entity_id: str | None
    before_snapshot: str | None
    after_snapshot: str | None
    description: str | None
    ip_address: str | None
    user_agent: str | None
    actor_name: str = ""
