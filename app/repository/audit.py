from app.models import AuditLog
from app.enums import AuditActionType
from sqlalchemy import select as _aselect
from .base import Page as _APage, BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)



class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def find_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        page: int = 1,
        per_page: int = 50,
    ) -> _APage[AuditLog]:
        stmt = (
            _aselect(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc())
        )
        return self.paginate(stmt, page=page, per_page=per_page)

    def find_by_actor(
        self,
        actor_id: str,
        page: int = 1,
        per_page: int = 50,
    ) -> _APage[AuditLog]:
        stmt = (
            _aselect(AuditLog)
            .where(AuditLog.actor_id == actor_id)
            .order_by(AuditLog.created_at.desc())
        )
        return self.paginate(stmt, page=page, per_page=per_page)

    def find_by_action(self, action: AuditActionType) -> list[AuditLog]:
        stmt = (
            _aselect(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
        )
        return list(self._session.execute(stmt).scalars().all())

    # AuditLog is IMMUTABLE — no update or delete methods exposed.
    def update(self, *args, **kwargs):
        raise NotImplementedError("AuditLog records are immutable.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("AuditLog records are immutable.")
