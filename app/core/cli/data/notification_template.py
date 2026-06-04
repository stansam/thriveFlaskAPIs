from datetime import datetime, timezone
from app.enums import NotificationEventType, NotificationChannel

NOTIFICATION_TEMPLATES = [
    {
        "id": f"00000000-0000-0000-0017-{i:012d}",
        "event_type": NotificationEventType.USER_PASSWORD_RESET if i == 1
                     else (NotificationEventType.USER_PASSWORD_CHANGED if i == 2
                     else (NotificationEventType.USER_MFA_ENROLLED if i == 3
                     else (NotificationEventType.USER_MFA_DISABLED if i == 4
                     else (NotificationEventType.BOOKING_CREATED if i == 5
                     else (NotificationEventType.BOOKING_CONFIRMED if i == 6
                     else (NotificationEventType.CLIENT_WELCOME if i == 7
                     else NotificationEventType.PACKAGE_PUBLISHED)))))),
        "channel": NotificationChannel.EMAIL if i % 2 == 0 else NotificationChannel.IN_APP,
        "language": "en",
        "name": f"Template Name {i}",
        "subject": f"Subject for Event {i}" if i % 2 == 0 else None,
        "body": f"Hello, this is the body template for event {i}. Details: {{{{ detail_var }}}}.",
        "variable_schema": '{"type": "object", "properties": {"detail_var": {"type": "string"}}}',
        "version": 1,
        "is_active": True,
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
