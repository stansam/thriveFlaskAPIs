from datetime import datetime, timezone
from app.enums import AuditActionType

AUDITS = [
    {
        "id": f"00000000-0000-0000-001a-{i:012d}",
        "actor_id": f"00000000-0000-0000-0000-{i:012d}",
        "action": AuditActionType.CREATE if i % 2 == 0 else AuditActionType.UPDATE,
        "entity_type": "booking" if i % 2 == 0 else "client",
        "entity_id": f"00000000-0000-0000-0010-000000000{100+i:03d}" if i % 2 == 0 else f"00000000-0000-0000-0004-{i:012d}",
        "before_snapshot": '{"status": "pending"}' if i % 2 != 0 else None,
        "after_snapshot": '{"status": "confirmed"}' if i % 2 == 0 else '{"status": "active"}',
        "description": f"Audited event {i} description here.",
        "ip_address": "127.0.0.1",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": f"00000000-0000-0000-0000-{i:012d}",
        "updated_by_id": f"00000000-0000-0000-0000-{i:012d}",
    }
    for i in range(1, 16)
]
