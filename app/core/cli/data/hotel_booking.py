from datetime import date, datetime, timezone
from decimal import Decimal
from app.enums import BookingServiceType, BookingStatus, RoomType

HOTEL_BOOKINGS = [
    {
        "id": f"00000000-0000-0000-0010-000000000{200+i:03d}",
        "reference_number": f"TG-2026-HTL{i:03d}",
        "service_type": BookingServiceType.HOTEL,
        "status": BookingStatus.CONFIRMED if i % 2 == 0 else BookingStatus.PENDING_PAYMENT,
        "client_id": f"00000000-0000-0000-0004-{i:012d}",
        "total_service_fee_usd": Decimal("20.00"),
        "ticket_cost_usd": Decimal(f"{200.00 * i:.2f}"),
        "currency": "USD",
        "discount_amount_usd": Decimal("0.00"),
        "is_emergency": False,
        "is_group": False,
        "agent_notes": f"Hotel booking {i} processed successfully.",
        "client_notes": f"High floor preferred.",
        "confirmed_at": datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc) if i % 2 == 0 else None,
        "cancelled_at": None,
        "completed_at": None,
        "hotel_name": f"Luxury Ritz {i}",
        "hotel_address": f"{10 * i} Resort Way, Miami, FL 33101",
        "hotel_city": "Miami",
        "hotel_country": "United States",
        "star_rating": 5,
        "room_type": RoomType.DELUXE if i % 3 == 0 else (RoomType.SUITE if i % 3 == 1 else RoomType.STANDARD),
        "num_rooms": 1,
        "num_guests": 2,
        "check_in_date": date(2026, 7, i),
        "check_out_date": date(2026, 7, i + 5),
        "confirmation_number": f"CONF-HTL-{2000 + i}",
        "special_requests": "Late check-in.",
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
