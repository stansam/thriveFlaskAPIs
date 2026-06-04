from datetime import datetime, timezone
from decimal import Decimal
from app.enums import BookingServiceType, BookingStatus, CarCategory

CAR_BOOKINGS = [
    {
        "id": f"00000000-0000-0000-0010-000000000{i:03d}",
        "reference_number": f"TG-2026-CAR{i:03d}",
        "service_type": BookingServiceType.CAR,
        "status": BookingStatus.CONFIRMED if i % 2 == 0 else BookingStatus.PENDING_PAYMENT,
        "client_id": f"00000000-0000-0000-0004-{i:012d}",
        "total_service_fee_usd": Decimal("15.00"),
        "ticket_cost_usd": Decimal(f"{100.00 * i:.2f}"),
        "currency": "USD",
        "discount_amount_usd": Decimal("0.00"),
        "is_emergency": False,
        "is_group": False,
        "agent_notes": f"Car booking {i} processed successfully.",
        "client_notes": f"Please ensure child seat is included.",
        "confirmed_at": datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc) if i % 2 == 0 else None,
        "cancelled_at": None,
        "completed_at": None,
        "rental_company": "Hertz" if i % 2 == 0 else "Avis",
        "pickup_location": "JFK Airport, NY",
        "dropoff_location": None,
        "pickup_datetime": datetime(2026, 7, i, 12, 0, 0, tzinfo=timezone.utc),
        "dropoff_datetime": datetime(2026, 7, i + 3, 12, 0, 0, tzinfo=timezone.utc),
        "car_category": CarCategory.SUV if i % 3 == 0 else (CarCategory.LUXURY if i % 3 == 1 else CarCategory.ECONOMY),
        "num_passengers": 2,
        "confirmation_number": f"CONF-CAR-{1000 + i}",
        "driver_age": 30 + i,
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]
