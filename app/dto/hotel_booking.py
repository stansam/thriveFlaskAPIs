from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, model_validator

from app.enums import (
    BookingStatus, BookingServiceType,
    RoomType
)
from .common import AuditFieldsMixin, StrictRequestModel
from .client import ClientSummaryResponse
from .booking_passenger import BookingPassengerCreateRequest

class HotelBookingCreateRequest(StrictRequestModel):
    client_id:       str
    hotel_name:      Annotated[str, Field(min_length=2, max_length=300)]
    hotel_address:   str | None = None
    hotel_city:      Annotated[str, Field(min_length=1, max_length=100)]
    hotel_country:   Annotated[str, Field(min_length=1, max_length=100)]
    star_rating:     Annotated[int | None, Field(default=None, ge=1, le=5)]
    room_type:       RoomType = RoomType.STANDARD
    num_rooms:       Annotated[int, Field(ge=1)] = 1
    num_guests:      Annotated[int, Field(ge=1)] = 1
    check_in_date:   date
    check_out_date:  date
    special_requests: str | None = None
    is_emergency:    bool = False
    client_notes:    str | None = None
    passengers:      list[BookingPassengerCreateRequest] = []

    @model_validator(mode="after")
    def checkout_after_checkin(self) -> "HotelBookingCreateRequest":
        if self.check_out_date <= self.check_in_date:
            raise ValueError("check_out_date must be after check_in_date.")
        return self

class HotelBookingUpdateRequest(StrictRequestModel):
    hotel_name:           str | None = None
    hotel_address:        str | None = None
    star_rating:          int | None = None
    room_type:            RoomType | None = None
    num_rooms:            int | None = None
    check_in_date:        date | None = None
    check_out_date:       date | None = None
    confirmation_number:  Annotated[str | None, Field(default=None, max_length=50)]
    special_requests:     str | None = None
    agent_notes:          str | None = None
    ticket_cost_usd:      Decimal | None = None

class HotelBookingResponse(AuditFieldsMixin):
    reference_number:      str
    service_type:          BookingServiceType
    status:                BookingStatus
    client_id:             str
    client:                ClientSummaryResponse | None = None
    hotel_name:            str
    hotel_address:         str | None
    hotel_city:            str
    hotel_country:         str
    star_rating:           int | None
    room_type:             RoomType
    num_rooms:             int
    num_guests:            int
    check_in_date:         date
    check_out_date:        date
    confirmation_number:   str | None
    special_requests:      str | None
    is_emergency:          bool
    total_service_fee_usd: Decimal
    ticket_cost_usd:       Decimal | None
    discount_amount_usd:   Decimal
    agent_notes:           str | None
    client_notes:          str | None
    confirmed_at:          datetime | None
    cancelled_at:          datetime | None
    completed_at:          datetime | None
    passengers:            list[BookingPassengerResponse] = []
