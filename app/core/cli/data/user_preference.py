from datetime import datetime, timezone
from app.enums import ThemePreference, DashboardLayout, PreferredChannel

USER_PREFERENCES = [
    {
        "id": f"00000000-0000-0000-0001-{i:012d}",
        "user_id": f"00000000-0000-0000-0000-{i:012d}",
        "theme": ThemePreference.LIGHT if i % 3 == 0 else (ThemePreference.DARK if i % 3 == 1 else ThemePreference.SYSTEM),
        "timezone": "America/New_York" if i % 2 == 0 else "UTC",
        "language": "en",
        "dashboard_layout": DashboardLayout.OVERVIEW if i % 2 == 0 else DashboardLayout.BOOKINGS,
        "items_per_page": 25 + (i * 5) % 50,
        "default_booking_channel": PreferredChannel.WHATSAPP if i % 2 == 0 else PreferredChannel.EMAIL,
        "show_ticket_cost_column": True,
        "auto_send_confirmation": True,
        "notify_new_booking": True,
        "notify_payment_received": True,
        "notify_booking_cancelled": True,
        "notify_booking_confirmed": True,
        "notify_new_client": i % 2 == 0,
        "notify_referral_qualified": True,
        "notify_subscription_renewal": True,
        "notify_low_stock_alert": i % 2 != 0,
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": f"00000000-0000-0000-0000-{i:012d}",
        "updated_by_id": f"00000000-0000-0000-0000-{i:012d}",
    }
    for i in range(1, 16)
]
