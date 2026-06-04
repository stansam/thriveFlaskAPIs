from datetime import datetime, timezone
from decimal import Decimal
from app.enums import BookingChannel, FeeType

FEE_SNAPSHOTS = [
    {
        "id": f"00000000-0000-0000-0013-{i:012d}",
        "booking_id": f"00000000-0000-0000-0010-000000000{100+i:03d}",  # Flight bookings
        "fee_id": "00000000-0000-0000-0007-000000000002" if i % 2 == 0 else "00000000-0000-0000-0007-000000000001",
        "fee_type": FeeType.INTERNATIONAL_FLIGHT if i % 2 == 0 else FeeType.DOMESTIC_FLIGHT,
        "fee_label": "International Flight Booking Fee" if i % 2 == 0 else "Domestic Flight Booking Fee",
        "base_amount_usd": Decimal("50.00") if i % 2 == 0 else Decimal("15.00"),
        "applied_amount_usd": Decimal("50.00") if i % 2 == 0 else Decimal("15.00"),
        "num_passengers": 1,
        "channel": BookingChannel.WHATSAPP if i % 2 == 0 else BookingChannel.EMAIL,
        "emergency_surcharge_applied": False,
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
