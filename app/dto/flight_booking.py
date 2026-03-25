from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from app.enums import (
    BookingStatus, BookingServiceType,
    FlightCabin
)
from .common import AuditFieldsMixin, StrictRequestModel
from .client import ClientSummaryResponse
from .booking_passenger import BookingPassengerCreateRequest, BookingPassengerResponse

# FLIGHT SEGMENT
class FlightSegmentCreateRequest(StrictRequestModel):
    segment_order:      Annotated[int, Field(ge=1)]
    origin_iata:        Annotated[str, Field(min_length=3, max_length=3)]
    destination_iata:   Annotated[str, Field(min_length=3, max_length=3)]
    airline_code:       Annotated[str | None, Field(default=None, min_length=2, max_length=3)]
    flight_number:      Annotated[str | None, Field(default=None, max_length=10)]
    departure_datetime: datetime | None = None
    arrival_datetime:   datetime | None = None
    duration_minutes:   int | None = None
    aircraft_type:      Annotated[str | None, Field(default=None, max_length=10)]

    @field_validator("origin_iata", "destination_iata", "airline_code", mode="before")
    @classmethod
    def upper(cls, v: str | None) -> str | None:
        return v.upper().strip() if v else v

class FlightSegmentResponse(AuditFieldsMixin):
    flight_booking_id:  str
    segment_order:      int
    origin_iata:        str
    destination_iata:   str
    airline_code:       str | None
    flight_number:      str | None
    departure_datetime: datetime | None
    arrival_datetime:   datetime | None
    duration_minutes:   int | None
    aircraft_type:      str | None

# FLIGHT BOOKING
class FlightBookingCreateRequest(StrictRequestModel):
    """POST /bookings/flights"""
    client_id:         str
    origin_iata:       Annotated[str, Field(min_length=3, max_length=3)]
    destination_iata:  Annotated[str, Field(min_length=3, max_length=3)]
    departure_date:    date
    return_date:       date | None = None
    is_round_trip:     bool = True
    is_international:  bool = False
    cabin_class:       FlightCabin = FlightCabin.ECONOMY
    num_adults:        Annotated[int, Field(ge=1)] = 1
    num_children:      Annotated[int, Field(ge=0)] = 0
    num_infants:       Annotated[int, Field(ge=0)] = 0
    is_emergency:      bool = False
    is_group:          bool = False
    client_notes:      Annotated[str | None, Field(default=None, max_length=2000)]
    # Passenger manifest (at least one required)
    passengers: Annotated[list[BookingPassengerCreateRequest], Field(min_length=1)]
    # Segments — may be added later via separate endpoint
    segments: list[FlightSegmentCreateRequest] = []

    @field_validator("origin_iata", "destination_iata", mode="before")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper().strip()

    @model_validator(mode="after")
    def round_trip_needs_return(self) -> "FlightBookingCreateRequest":
        if self.is_round_trip and not self.return_date:
            raise ValueError("return_date is required for round-trip bookings.")
        return self

    @model_validator(mode="after")
    def group_needs_five(self) -> "FlightBookingCreateRequest":
        total = self.num_adults + self.num_children
        if self.is_group and total < 5:
            raise ValueError("Group bookings require at least 5 passengers.")
        return self

class FlightBookingUpdateRequest(StrictRequestModel):
    """PATCH /bookings/flights/{id}"""
    pnr:                Annotated[str | None, Field(default=None, max_length=20)]
    airline_booking_url: Annotated[str | None, Field(default=None, max_length=2048)]
    cabin_class:        FlightCabin | None = None
    agent_notes:        Annotated[str | None, Field(default=None, max_length=2000)]
    ticket_cost_usd:    Decimal | None = None
    ticket_issued_at:   datetime | None = None

class FlightBookingResponse(AuditFieldsMixin):
    reference_number:    str
    service_type:        BookingServiceType
    status:              BookingStatus
    client_id:           str
    client:              ClientSummaryResponse | None = None
    origin_iata:         str
    destination_iata:    str
    departure_date:      date
    return_date:         date | None
    is_round_trip:       bool
    is_international:    bool
    cabin_class:         FlightCabin
    num_adults:          int
    num_children:        int
    num_infants:         int
    pnr:                 str | None
    airline_booking_url: str | None
    ticket_issued_at:    datetime | None
    is_emergency:        bool
    is_group:            bool
    total_service_fee_usd: Decimal
    ticket_cost_usd:     Decimal | None
    discount_amount_usd: Decimal
    currency:            str
    agent_notes:         str | None
    client_notes:        str | None
    confirmed_at:        datetime | None
    cancelled_at:        datetime | None
    completed_at:        datetime | None
    segments:            list[FlightSegmentResponse] = []
    passengers:          list[BookingPassengerResponse] = []
