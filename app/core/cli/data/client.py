from datetime import date, datetime, timezone
from app.enums import ClientType

CLIENTS = [
    {
        "id": f"00000000-0000-0000-0004-{i:012d}",
        "first_name": f"First{i}",
        "last_name": f"Last{i}",
        "email": f"client{i}@gmail.com",
        "phone": f"+1555040{i:02d}",
        "whatsapp_number": f"+1555040{i:02d}",
        "nationality": "United States" if i % 2 == 0 else "United Kingdom",
        "passport_number": f"PASS-{100000 + i}",
        "passport_expiry": date(2030, 1, 1),
        "date_of_birth": date(1985, i % 12 + 1, 15),
        "preferred_language": "en",
        "client_type": ClientType.CORPORATE if i % 3 == 0 else ClientType.INDIVIDUAL,
        "is_group_leader": i % 5 == 0,
        "is_active": True,
        "notes": f"VIP customer number {i} notes here.",
        "corporate_account_id": f"00000000-0000-0000-0002-{i:012d}" if i % 3 == 0 else None,
        "referred_by_id": f"00000000-0000-0000-0004-{(i-1):012d}" if i > 1 and i % 4 == 0 else None,
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
