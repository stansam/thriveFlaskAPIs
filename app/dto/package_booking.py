from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from app.enums import (
    BookingStatus, BookingServiceType,
)
from .common import AuditFieldsMixin, StrictRequestModel
from .client import ClientSummaryResponse
from .booking_passenger import BookingPassengerCreateRequest, BookingPassengerResponse

class PackageBookingCreateRequest(StrictRequestModel):
    client_id:             str
    package_id:            str
    selected_price_tier_id: str | None = None
    num_participants:      Annotated[int, Field(ge=1)] = 1
    travel_date:           date
    return_date:           date | None = None
    add_flights:           bool = False
    add_insurance:         bool = False
    customisation_notes:   str | None = None
    is_emergency:          bool = False
    client_notes:          str | None = None
    passengers:            list[BookingPassengerCreateRequest] = []

class PackageBookingUpdateRequest(StrictRequestModel):
    selected_price_tier_id: str | None = None
    num_participants:       int | None = None
    travel_date:            date | None = None
    return_date:            date | None = None
    add_flights:            bool | None = None
    add_insurance:          bool | None = None
    customisation_notes:    str | None = None
    agent_notes:            str | None = None
    ticket_cost_usd:        Decimal | None = None
    linked_flight_booking_id: str | None = None

class PackageBookingResponse(AuditFieldsMixin):
    reference_number:        str
    service_type:            BookingServiceType
    status:                  BookingStatus
    client_id:               str
    client:                  ClientSummaryResponse | None = None
    package_id:              str
    selected_price_tier_id:  str | None
    num_participants:        int
    travel_date:             date
    return_date:             date | None
    add_flights:             bool
    add_insurance:           bool
    linked_flight_booking_id: str | None
    price_per_person_usd:    Decimal
    total_package_cost_usd:  Decimal
    customisation_notes:     str | None
    is_emergency:            bool
    total_service_fee_usd:   Decimal
    ticket_cost_usd:         Decimal | None
    discount_amount_usd:     Decimal
    agent_notes:             str | None
    client_notes:            str | None
    confirmed_at:            datetime | None
    cancelled_at:            datetime | None
    completed_at:            datetime | None
    passengers:              list[BookingPassengerResponse] = []

