from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from app.models.enums import TravelClass

@dataclass
class PassengerQueryDTO:
    adults: int
    children: int = 0
    infants: int = 0

@dataclass
class SearchFlightDTO:
    origin: str
    destination: str
    departure_date: datetime
    cabin_class: TravelClass
    currency: str
    passengers: PassengerQueryDTO
    return_date: Optional[datetime] = None
    page: int = 1

@dataclass
class FlightSegmentDTO:
    carrier_code: str
    flight_number: str
    departure_airport_code: str
    arrival_airport_code: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: Optional[int] = None
    aircraft_type: Optional[str] = None
    baggage_allowance: Optional[str] = None
    terminal: Optional[str] = None
    gate: Optional[str] = None

@dataclass
class BookFlightDTO:
    user_id: str
    cabin_class: TravelClass
    segments: List[FlightSegmentDTO]
    pnr_reference: Optional[str] = None
