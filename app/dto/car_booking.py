from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, model_validator

from app.enums import (
    BookingStatus, BookingServiceType,
    CarCategory
)
from .common import AuditFieldsMixin, StrictRequestModel
from .client import ClientSummaryResponse
from .booking_passenger import BookingPassengerCreateRequest, BookingPassengerResponse

class CarBookingCreateRequest(StrictRequestModel):
    client_id:         str
    rental_company:    Annotated[str | None, Field(default=None, max_length=200)]
    pickup_location:   Annotated[str, Field(min_length=2, max_length=300)]
    dropoff_location:  Annotated[str | None, Field(default=None, max_length=300)]
    pickup_datetime:   datetime
    dropoff_datetime:  datetime
    car_category:      CarCategory = CarCategory.ECONOMY
    num_passengers:    Annotated[int, Field(ge=1)] = 1
    driver_age:        Annotated[int | None, Field(default=None, ge=18, le=99)]
    is_emergency:      bool = False
    client_notes:      str | None = None
    passengers:        list[BookingPassengerCreateRequest] = []

    @model_validator(mode="after")
    def dropoff_after_pickup(self) -> "CarBookingCreateRequest":
        if self.dropoff_datetime <= self.pickup_datetime:
            raise ValueError("dropoff_datetime must be after pickup_datetime.")
        return self


class CarBookingUpdateRequest(StrictRequestModel):
    rental_company:       str | None = None
    pickup_location:      str | None = None
    dropoff_location:     str | None = None
    pickup_datetime:      datetime | None = None
    dropoff_datetime:     datetime | None = None
    car_category:         CarCategory | None = None
    confirmation_number:  Annotated[str | None, Field(default=None, max_length=50)]
    agent_notes:          str | None = None
    ticket_cost_usd:      Decimal | None = None


class CarBookingResponse(AuditFieldsMixin):
    reference_number:      str
    service_type:          BookingServiceType
    status:                BookingStatus
    client_id:             str
    client:                ClientSummaryResponse | None = None
    rental_company:        str | None
    pickup_location:       str
    dropoff_location:      str | None
    pickup_datetime:       datetime
    dropoff_datetime:      datetime
    car_category:          CarCategory
    num_passengers:        int
    driver_age:            int | None
    confirmation_number:   str | None
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
