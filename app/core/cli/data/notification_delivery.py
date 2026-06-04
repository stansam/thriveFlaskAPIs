from datetime import datetime, timezone
from app.enums import NotificationChannel, DeliveryStatus

NOTIFICATIONS_DELIVERIES = [
    {
        "id": f"00000000-0000-0000-0019-{i:012d}",
        "notification_id": f"00000000-0000-0000-0018-{i:012d}",
        "channel": NotificationChannel.EMAIL if i % 2 == 0 else NotificationChannel.WHATSAPP,
        "status": DeliveryStatus.DELIVERED if i % 2 == 0 else DeliveryStatus.SENT,
        "recipient_address": f"client{i}@gmail.com" if i % 2 == 0 else f"+1555040{i:02d}",
        "provider_name": "sendgrid" if i % 2 == 0 else "twilio",
        "provider_message_id": f"msg-id-{1000 + i}",
        "provider_response_json": '{"status": "ok"}',
        "attempt_number": 1,
        "sent_at": datetime(2026, 6, 1, 0, 1, 0, tzinfo=timezone.utc),
        "delivered_at": datetime(2026, 6, 1, 0, 2, 0, tzinfo=timezone.utc) if i % 2 == 0 else None,
        "opened_at": datetime(2026, 6, 1, 1, 0, 0, tzinfo=timezone.utc) if i % 4 == 0 else None,
        "failed_at": None,
        "failure_reason": None,
        "next_retry_at": None,
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
