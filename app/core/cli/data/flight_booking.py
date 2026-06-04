from datetime import date, datetime, timezone
from decimal import Decimal
from app.enums import BookingServiceType, BookingStatus, FlightCabin

FLIGHT_BOOKINGS = [
    {
        "id": f"00000000-0000-0000-0010-000000000{100+i:03d}",
        "reference_number": f"TG-2026-FLT{i:03d}",
        "service_type": BookingServiceType.FLIGHT,
        "status": BookingStatus.CONFIRMED if i % 2 == 0 else BookingStatus.PENDING_PAYMENT,
        "client_id": f"00000000-0000-0000-0004-{i:012d}",
        "total_service_fee_usd": Decimal("50.00") if i % 2 == 0 else Decimal("15.00"),
        "ticket_cost_usd": Decimal(f"{300.00 * i:.2f}"),
        "currency": "USD",
        "discount_amount_usd": Decimal("0.00"),
        "is_emergency": False,
        "is_group": False,
        "agent_notes": f"Flight booking {i} processed.",
        "client_notes": f"Aisle seat requested.",
        "confirmed_at": datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc) if i % 2 == 0 else None,
        "cancelled_at": None,
        "completed_at": None,
        "origin_iata": "JFK",
        "destination_iata": "LHR" if i % 2 == 0 else "LAX",
        "departure_date": date(2026, 8, i),
        "return_date": date(2026, 8, i + 7) if i % 3 != 0 else None,
        "is_round_trip": i % 3 != 0,
        "cabin_class": FlightCabin.BUSINESS if i % 4 == 0 else FlightCabin.ECONOMY,
        "num_adults": 1,
        "num_children": 0,
        "num_infants": 0,
        "pnr": f"PNRFL{i:02d}",
        "airline_booking_url": f"https://airline.com/booking/PNRFL{i:02d}",
        "ticket_issued_at": datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc) if i % 2 == 0 else None,
        "is_international": i % 2 == 0,
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 16)
]

FLIGHT_SEGMENTS = [
    {
        "id": f"00000000-0000-0000-0012-{i:012d}",
        "flight_booking_id": f"00000000-0000-0000-0010-000000000{100+(i if i <= 15 else i-15):03d}",
        "segment_order": 1 if i <= 15 else 2,
        "origin_iata": "JFK" if i <= 15 else ("LHR" if i % 2 == 0 else "LAX"),
        "destination_iata": ("LHR" if i % 2 == 0 else "LAX") if i <= 15 else "DXB",
        "airline_code": "BA" if i % 2 == 0 else "AA",
        "flight_number": f"1{i:02d}",
        "departure_datetime": datetime(2026, 8, i if i <= 15 else i-15, 10, 0, 0, tzinfo=timezone.utc),
        "arrival_datetime": datetime(2026, 8, i if i <= 15 else i-15, 18, 0, 0, tzinfo=timezone.utc),
        "duration_minutes": 480,
        "aircraft_type": "B777" if i % 2 == 0 else "A350",
        "created_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        "created_by_id": "00000000-0000-0000-0000-000000000001",
        "updated_by_id": "00000000-0000-0000-0000-000000000001",
    }
    for i in range(1, 21)  # 20 segments to ensure some connecting flights
]
