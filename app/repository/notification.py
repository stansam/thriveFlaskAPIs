from sqlalchemy import select as _nselect
from app.models import Notification, NotificationTemplate
from app.enums import (
    NotificationStatus, NotificationEventType,
    NotificationChannel, RecipientType,
)
from .base import Page as _Page, BaseRepository


class NotificationTemplateRepository(BaseRepository[NotificationTemplate]):
    model = NotificationTemplate

    def find_for_event(
        self,
        event_type: NotificationEventType,
        channel: NotificationChannel,
        language: str = "en",
    ) -> NotificationTemplate | None:
        """Find best-match template; falls back to 'en' if preferred language missing."""
        stmt = (
            _nselect(NotificationTemplate)
            .where(
                NotificationTemplate.event_type == event_type,
                NotificationTemplate.channel == channel,
                NotificationTemplate.language == language,
                NotificationTemplate.is_active.is_(True),
            )
        )
        result = self._session.execute(stmt).scalar_one_or_none()
        if result is None and language != "en":
            return self.find_for_event(event_type, channel, "en")
        return result

    def find_all_for_event(
        self, event_type: NotificationEventType
    ) -> list[NotificationTemplate]:
        stmt = (
            _nselect(NotificationTemplate)
            .where(
                NotificationTemplate.event_type == event_type,
                NotificationTemplate.is_active.is_(True),
            )
            .order_by(NotificationTemplate.channel, NotificationTemplate.language)
        )
        return list(self._session.execute(stmt).scalars().all())


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    def find_for_recipient(
        self,
        recipient_type: RecipientType,
        recipient_id: str,
        unread_only: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> _Page[Notification]:
        stmt = (
            _nselect(Notification)
            .where(
                Notification.recipient_type == recipient_type,
                Notification.recipient_id == recipient_id,
            )
        )
        if unread_only:
            stmt = stmt.where(
                Notification.status.not_in([
                    NotificationStatus.READ,
                    NotificationStatus.DISMISSED,
                ])
            )
        stmt = stmt.order_by(Notification.created_at.desc())
        return self.paginate(stmt, page=page, per_page=per_page)

    def unread_count(self, recipient_type: RecipientType, recipient_id: str) -> int:
        from sqlalchemy import func
        stmt = (
            _nselect(func.count(Notification.id))
            .where(
                Notification.recipient_type == recipient_type,
                Notification.recipient_id == recipient_id,
                Notification.status.not_in([
                    NotificationStatus.READ,
                    NotificationStatus.DISMISSED,
                ]),
            )
        )
        return self._session.execute(stmt).scalar_one()

    def mark_read(
        self,
        notification: Notification,
        actor_id: str | None = None,
    ) -> Notification:
        from datetime import datetime
        return self.update(
            notification,
            actor_id=actor_id,
            status=NotificationStatus.READ,
            read_at=datetime.utcnow(),
        )

    def mark_all_read(
        self,
        recipient_type: RecipientType,
        recipient_id: str,
    ) -> int:
        """Bulk mark all unread notifications as read. Returns count updated."""
        from datetime import datetime
        notifications = self._session.execute(
            _nselect(Notification).where(
                Notification.recipient_type == recipient_type,
                Notification.recipient_id == recipient_id,
                Notification.status.not_in([
                    NotificationStatus.READ,
                    NotificationStatus.DISMISSED,
                ]),
            )
        ).scalars().all()
        now = datetime.utcnow()
        for n in notifications:
            n.status = NotificationStatus.READ
            n.read_at = now
        self._session.flush()
        return len(notifications)

    def find_scheduled_ready(self, as_of=None) -> list[Notification]:
        from datetime import datetime
        now = as_of or datetime.utcnow()
        stmt = (
            _nselect(Notification)
            .where(
                Notification.status == NotificationStatus.PENDING,
                Notification.scheduled_for <= now,
            )
            .order_by(Notification.scheduled_for)
        )
        return list(self._session.execute(stmt).scalars().all())



