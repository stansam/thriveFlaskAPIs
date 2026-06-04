from datetime import datetime, timezone
from app.enums import PreferredChannel, DocumentFormat

CLIENT_PREFERENCES = [
    {
        "id": f"00000000-0000-0000-0005-{i:012d}",
        "client_id": f"00000000-0000-0000-0004-{i:012d}",
        "preferred_channel": PreferredChannel.WHATSAPP if i % 2 == 0 else PreferredChannel.EMAIL,
        "preferred_document_format": DocumentFormat.PDF if i % 2 == 0 else DocumentFormat.EMAIL,
        "marketing_opt_in": True,
        "booking_reminders": True,
        "travel_reminder_hours": 48,
        "payment_reminders": True,
        "language": "en",
        "preferred_currency_display": "USD",
        "timezone": "UTC" if i % 2 == 0 else "America/New_York",
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
