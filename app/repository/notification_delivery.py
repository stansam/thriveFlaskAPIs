from sqlalchemy import select as _nselect

from app.models import NotificationDelivery
from app.enums import DeliveryStatus
from .base import BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)



class NotificationDeliveryRepository(BaseRepository[NotificationDelivery]):
    model = NotificationDelivery

    def find_by_notification(self, notification_id: str) -> list[NotificationDelivery]:
        stmt = (
            _nselect(NotificationDelivery)
            .where(NotificationDelivery.notification_id == notification_id)
            .order_by(NotificationDelivery.channel, NotificationDelivery.attempt_number)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_retryable(self, as_of=None) -> list[NotificationDelivery]:
        from datetime import datetime
        now = as_of or datetime.utcnow()
        stmt = (
            _nselect(NotificationDelivery)
            .where(
                NotificationDelivery.status == DeliveryStatus.RETRYING,
                NotificationDelivery.next_retry_at <= now,
            )
            .order_by(NotificationDelivery.next_retry_at)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_by_provider_message_id(self, msg_id: str) -> NotificationDelivery | None:
        return self.get_by(provider_message_id=msg_id)
