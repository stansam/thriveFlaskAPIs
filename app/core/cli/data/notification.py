from datetime import datetime, timezone
from app.enums import NotificationEventType, RecipientType, NotificationStatus, NotificationPriority

NOTIFICATIONS = [
    {
        "id": f"00000000-0000-0000-0018-{i:012d}",
        "template_id": f"00000000-0000-0000-0017-{i:012d}",
        "event_type": NotificationEventType.CLIENT_WELCOME if i == 7 else NotificationEventType.BOOKING_CREATED,
        "recipient_type": RecipientType.CLIENT,
        "recipient_id": f"00000000-0000-0000-0004-{i:012d}",
        "title": f"Rendered Title {i}",
        "body": f"Rendered Body description for notification {i}.",
        "context_json": '{"detail_var": "Sample details"}',
        "entity_type": "booking" if i != 7 else None,
        "entity_id": f"00000000-0000-0000-0010-000000000{100+i:03d}" if i != 7 else None,
        "status": NotificationStatus.DELIVERED if i % 2 == 0 else NotificationStatus.PENDING,
        "priority": NotificationPriority.NORMAL,
        "read_at": datetime(2026, 6, 2, 12, 0, 0, tzinfo=timezone.utc) if i % 4 == 0 else None,
        "dismissed_at": None,
        "scheduled_for": None,
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
