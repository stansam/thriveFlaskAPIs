# app/dto/flight_adapter.py
"""
Flight search request definitions and response models.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from datetime import date

from app.core.errors.handlers import BadRequestError
from app.enums import PassengerType, SortMode

_IATA_RE = re.compile(r"^[A-Z]{2,4}$")


@dataclass
class FlightSearchRequest:
    origin: str
    destination: str
    departure_date: date
    return_date: date | None = None
    passengers: list[PassengerType] = field(default_factory=lambda: [PassengerType.ADT])
    filter_string: str = ""
    sort_mode: SortMode = SortMode.BEST
    page_number: int = 1
    search_id: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.origin, str):
            self.origin = self.origin.strip().upper()
        if isinstance(self.destination, str):
            self.destination = self.destination.strip().upper()

        if not self.origin or not _IATA_RE.match(self.origin):
            raise BadRequestError(f"Origin must be a 2-4 letter IATA code: {self.origin!r}")
        if not self.destination or not _IATA_RE.match(self.destination):
            raise BadRequestError(f"Destination must be a 2-4 letter IATA code: {self.destination!r}")

        if not isinstance(self.departure_date, date):
            raise BadRequestError("Departure date must be a date object.")
        if self.return_date and not isinstance(self.return_date, date):
            raise BadRequestError("Return date must be a date object.")

        if self.departure_date < date.today():
            raise BadRequestError(f"Departure date {self.departure_date} cannot be in the past.")

        if self.return_date and self.return_date < self.departure_date:
            raise BadRequestError(
                f"Return date {self.return_date} cannot be before departure date {self.departure_date}."
            )

        if not self.passengers:
            raise BadRequestError("Passengers list cannot be empty.")

        validated_passengers = []
        for p in self.passengers:
            if isinstance(p, str):
                try:
                    validated_passengers.append(PassengerType(p.upper()))
                except ValueError:
                    raise BadRequestError(f"Invalid passenger type: {p!r}")
            elif isinstance(p, PassengerType):
                validated_passengers.append(p)
            else:
                raise BadRequestError(f"Invalid passenger type element: {p!r}")
        self.passengers = validated_passengers

        if not isinstance(self.page_number, int) or self.page_number < 1:
            raise BadRequestError(f"Page number must be an integer >= 1: {self.page_number!r}")

@dataclass
class FlightSegment:
    segment_id:       str
    origin:           str
    destination:      str
    departure:        str           # ISO datetime string
    arrival:          str
    airline_code:     str
    flight_number:    str
    duration_min:     int
    equipment_type:   str = ""      # "Airbus A321neo"
    cabin_code:       str = "e"
    cabin_display:    str = "Economy"


@dataclass
class FlightLegDetail:
    leg_id:       str
    departure:    str               # ISO datetime
    arrival:      str
    duration_min: int
    segments:     list[FlightSegment] = field(default_factory=list)


@dataclass
class BookingOption:
    booking_id:        str
    provider_code:     str
    booking_url:       str          # absolute URL (base + relative path)
    price_per_person:  float
    total_price:       float
    currency:          str = "USD"
    carry_on_status:   str = "UNKNOWN"   # "INCLUDED", "FEE", "UNKNOWN"
    checked_bag_status: str = "UNKNOWN"


@dataclass
class FlightOfferResult:
    result_id:          str
    trip_id:            str
    is_best:            bool = False
    is_cheapest:        bool = False
    legs:               list[FlightLegDetail] = field(default_factory=list)
    booking_options:    list[BookingOption] = field(default_factory=list)
    total_booking_options: int = 0
    shareable_url:      str = ""
    provider:           str = "kayak"
    raw:                dict[str, Any] = field(default_factory=dict)

    @property
    def best_price(self) -> float:
        """Return the lowest per-person price across all booking options."""
        if not self.booking_options:
            return 0.0
        return min(bo.price_per_person for bo in self.booking_options)

    @property
    def best_booking_url(self) -> str:
        if not self.booking_options:
            return ""
        return min(self.booking_options, key=lambda bo: bo.price_per_person).booking_url


@dataclass
class FlightSearchResponse:
    search_id:       str
    page_number:     int
    page_size:       int
    total_count:     int
    filtered_count:  int
    sort_mode:       str
    price_mode:      str
    status:          str
    results:         list[FlightOfferResult] = field(default_factory=list)
    regular_flights: int = 0


@dataclass
class PriceCheckResult:
    offer_id:    str
    price_usd:   float
    is_valid:    bool
    message:     str = ""


@dataclass
class FlightDetails:
    flight_number:        str
    airline_code:         str
    airline_name:         str
    origin:               str
    destination:          str
    departure_scheduled:  int        # unix ms
    arrival_scheduled:    int
    departure_delay_min:  int
    arrival_delay_min:    int
    duration_min:         int
    status_code:          str
    aircraft_type:        str = ""
    latitude:             float | None = None
    longitude:            float | None = None


@dataclass
class LocationResult:
    id:           str           # e.g. "MIA"
    airport_name: str
    city_name:    str
    display_name: str
    city:         str
    country:      str
    country_code: str
    lat:          float
    lng:          float
    timezone:     str