from datetime import datetime, timezone
from app.enums import UserRole

USERS = [
    {
        "id": f"00000000-0000-0000-0000-{i:012d}",
        "email": f"user{i}@thriveglobal.com",
        "full_name": f"Thrive Staff User {i}",
        "phone": f"+1555010{i:02d}",
        "password_hash": "$2b$12$EixZaYVK1fsdh1eg.O3.8e./tQ3e/C.Pvh8mJWcT0sX8x6vT5B7t.",  # bcrypt hash of "Password123!"
        "role": UserRole.SUPER_ADMIN if i <= 3 else (UserRole.ADMIN if i <= 7 else UserRole.AGENT),
        "is_active": True,
        "mfa_secret": "JBSWY3DPEHPK3PXP" if i % 2 == 0 else None,
        "last_login_at": datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        "failed_login_count": 0,
        "locked_until": None,
        "google_id": f"google-oauth-id-{i:012d}" if i % 3 == 0 else None,
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": None,
        "updated_by_id": None,
    }
    for i in range(1, 16)
]
