from datetime import date, datetime, timezone
from decimal import Decimal
from app.enums import BookingServiceType, BookingStatus

PACKAGE_BOOKINGS = [
    {
        "id": f"00000000-0000-0000-0010-000000000{300+i:03d}",
        "reference_number": f"TG-2026-PKG{i:03d}",
        "service_type": BookingServiceType.PACKAGE,
        "status": BookingStatus.CONFIRMED if i % 2 == 0 else BookingStatus.PENDING_PAYMENT,
        "client_id": f"00000000-0000-0000-0004-{i:012d}",
        "total_service_fee_usd": Decimal("100.00"),
        "ticket_cost_usd": Decimal(f"{1500.00 * i:.2f}"),
        "currency": "USD",
        "discount_amount_usd": Decimal("0.00"),
        "is_emergency": False,
        "is_group": False,
        "agent_notes": f"Package booking {i} processed successfully.",
        "client_notes": f"Special dietary requirements sent to package provider.",
        "confirmed_at": datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc) if i % 2 == 0 else None,
        "cancelled_at": None,
        "completed_at": None,
        "package_id": f"00000000-0000-0000-0008-{i:012d}",
        "selected_price_tier_id": f"00000000-0000-0000-000c-{i:012d}",
        "num_participants": 2,
        "travel_date": date(2026, 9, i),
        "return_date": date(2026, 9, i + 10),
        "add_flights": True,
        "add_insurance": True,
        "linked_flight_booking_id": f"00000000-0000-0000-0010-000000000{100+i:03d}" if i <= 15 else None,
        "price_per_person_usd": Decimal(f"{150.00 * i:.2f}"),
        "total_package_cost_usd": Decimal(f"{300.00 * i:.2f}"),
        "customisation_notes": "Bespoke tour modifications.",
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
