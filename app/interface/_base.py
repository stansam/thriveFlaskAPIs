# services/_base.py
"""
Shared base for all service classes.

Every service that mutates data should inherit BaseService and use the
`_audit()` helper instead of calling audit_repo directly.  This ensures
consistent audit log formatting across the entire service layer.

BaseService also provides:
  - `_page_to_dict` — converts a repository Page[Model] into a plain dict
    that Pydantic ResponseModels can be constructed from.
  - `_snapshot` — safely JSON-serialises an ORM object for before/after
    snapshots without triggering lazy-load queries.

Transaction contract (enforced by convention, not by code)
-----------------------------------------------------------
Every mutating public method must:
  1. Make all DB mutations (repo.create / repo.update etc.)
  2. Call `db.session.flush()` inside the repo (done automatically)
  3. Call `self._audit(...)` to write the audit entry
  4. Call `db.session.commit()` exactly once at the END
  5. Publish domain events AFTER the commit

Read-only methods never commit.
"""

from __future__ import annotations

import json
from typing import Any

from app.models.base import db
from app.enums import AuditActionType
from app.repository import audit_repo
from app.repository.base import Page
from app.core.logging import get_logger

logger = get_logger(__name__)

class BaseService:
    """Inherit from this in every concrete service class."""
    # Audit helper
    def _audit(
        self,
        action: AuditActionType,
        actor_id: str | None,
        entity_type: str,
        entity_id: str | None = None,
        description: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Write an immutable audit log row within the current transaction."""
        try:
            audit_repo.create(
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
        except Exception as exc:
            # Audit failures must NEVER break the main operation.
            # Log at ERROR so it surfaces in monitoring without raising.
            logger.error(
                "Audit write failed [%s %s/%s]: %s",
                action.value, entity_type, entity_id, exc,
            )
    # Snapshot helper
    @staticmethod
    def _snapshot(obj: Any, fields: list[str] | None = None) -> dict:
        """
        Build a JSON-safe dict from an ORM object for audit snapshots.
        Only includes scalar columns; skips relationships to avoid lazy loads.
        If `fields` is provided, only those fields are included.
        """
        if obj is None:
            return {}
        try:
            from sqlalchemy import inspect
            mapper = inspect(type(obj))
            col_names = [c.key for c in mapper.columns]
            if fields:
                col_names = [f for f in fields if f in col_names]
            return {
                k: getattr(obj, k, None)
                for k in col_names
                if not k.startswith("password")  # never snapshot passwords
            }
        except Exception:
            return {"id": getattr(obj, "id", None)}
    # Page conversion
    @staticmethod
    def _page_meta(page: Page) -> dict:
        """Return pagination metadata dict from a repository Page."""
        return {
            "total":       page.total,
            "page":        page.page,
            "per_page":    page.per_page,
            "total_pages": page.total_pages,
            "has_next":    page.has_next,
            "has_prev":    page.has_prev,
        }