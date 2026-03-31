# services/audit_service.py
"""
AuditService — immutable audit log management.

Implements interfaces.md § 16. AuditService.

The `log()` method is called internally by every service that mutates
data.  It should never be called directly by route handlers.

AuditLog rows are strictly immutable: no update or delete methods exist.
This is enforced both here (no such methods) and at the repository layer
(AuditLogRepository.update/delete raise NotImplementedError).
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import and_, select

from app.models.base import db
from app.enums import AuditActionType
from app.models import AuditLog
from app.core.errors.handlers import NotFoundError
from app.dto import AuditLogResponse
from app.repository import audit_repo, user_repo
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)

class AuditService(BaseService):
    # Write  (called internally by all mutating services)
    def log(
        self,
        actor_id:    str | None,
        action:      AuditActionType,
        entity_type: str,
        entity_id:   str | None = None,
        before:      dict | None = None,
        after:       dict | None = None,
        description: str | None = None,
        ip_address:  str | None = None,
        user_agent:  str | None = None,
        strict:      bool = True,
    ) -> AuditLog | None:
        """
        Write a single immutable audit log entry.

        This method flushes but does NOT commit.  The calling service owns
        the transaction and must commit after calling this.

        If `strict=True`, raises an exception if the audit log cannot be
        written. If `strict=False`, failures are logged at ERROR level
        and the method returns None to avoid breaking the parent operation.
        """
        try:
            entry = audit_repo.create(
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                before_snapshot=json.dumps(before, default=str) if before else None,
                after_snapshot=json.dumps(after, default=str) if after else None,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return entry
        except Exception as exc:
            logger.error(
                "AuditService.log failed [%s %s/%s]: %s",
                action.value, entity_type, entity_id, exc,
            )
            if strict:
                from app.core.errors.handlers import BusinessRuleViolationError # Or raise directly
                raise RuntimeError(f"Strict audit log writing failed: {str(exc)}") from exc
            return None
    # Read
    def get_entity_history(
        self,
        entity_type: str,
        entity_id:   str,
        page:        int = 1,
        per_page:    int = 50,
    ) -> dict:
        result = audit_repo.find_for_entity(
            entity_type, entity_id, page=page, per_page=per_page
        )
        return {
            "items": [_enrich(a) for a in result.items],
            **self._page_meta(result),
        }

    def get_actor_history(
        self,
        actor_id: str,
        page:     int = 1,
        per_page: int = 50,
    ) -> dict:
        user_repo.get_or_404(actor_id)
        result = audit_repo.find_by_actor(actor_id, page=page, per_page=per_page)
        return {
            "items": [_enrich(a) for a in result.items],
            **self._page_meta(result),
        }

    def list_audit_logs(
        self,
        action:      AuditActionType | None = None,
        entity_type: str | None = None,
        entity_id:   str | None = None,
        actor_id:    str | None = None,
        date_from:   date | None = None,
        date_to:     date | None = None,
        page:        int = 1,
        per_page:    int = 50,
    ) -> dict:
        stmt = select(AuditLog)

        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if date_from:
            from_dt = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
            stmt = stmt.where(AuditLog.created_at >= from_dt)
        if date_to:
            to_dt = datetime.combine(date_to, datetime.max.time(), tzinfo=timezone.utc)
            stmt = stmt.where(AuditLog.created_at <= to_dt)

        stmt = stmt.order_by(AuditLog.created_at.desc())
        result = audit_repo.paginate(stmt, page=page, per_page=per_page)
        return {
            "items": [_enrich(a) for a in result.items],
            **self._page_meta(result),
        }


def _enrich(a: AuditLog) -> AuditLogResponse:
    resp = AuditLogResponse.model_validate(a)
    if a.actor_id:
        try:
            actor = user_repo.get(a.actor_id)
            resp.actor_name = actor.full_name if actor else ""
        except Exception:
            pass
    return resp


audit_service = AuditService()