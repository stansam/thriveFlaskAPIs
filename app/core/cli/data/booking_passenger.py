from datetime import date, datetime, timezone

BOOKING_PASSENGERS = [
    {
        "id": f"00000000-0000-0000-0011-{i:012d}",
        "booking_id": f"00000000-0000-0000-0010-000000000{100+i:03d}",  # Flight bookings
        "client_id": f"00000000-0000-0000-0004-{i:012d}",
        "first_name": f"First{i}",
        "last_name": f"Last{i}",
        "date_of_birth": date(1985, i % 12 + 1, 15),
        "nationality": "United States" if i % 2 == 0 else "United Kingdom",
        "passport_number": f"PASS-{100000 + i}",
        "passport_expiry": date(2030, 1, 1),
        "is_lead_passenger": True,
        "seat_preference": "window" if i % 2 == 0 else "aisle",
        "meal_preference": "vegetarian" if i % 3 == 0 else "none",
        "special_assistance": "None",
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
