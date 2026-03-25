from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import Field

from .common import AuditFieldsMixin, StrictRequestModel

class BookingPassengerCreateRequest(StrictRequestModel):
    first_name:          Annotated[str, Field(min_length=1, max_length=100)]
    last_name:           Annotated[str, Field(min_length=1, max_length=100)]
    date_of_birth:       date | None = None
    nationality:         Annotated[str | None, Field(default=None, max_length=100)]
    passport_number:     Annotated[str | None, Field(default=None, max_length=50)]
    passport_expiry:     date | None = None
    is_lead_passenger:   bool = False
    seat_preference:     Annotated[str | None, Field(default=None, max_length=50)]
    meal_preference:     Annotated[str | None, Field(default=None, max_length=50)]
    special_assistance:  Annotated[str | None, Field(default=None, max_length=300)]
    client_id:           str | None = None


class BookingPassengerResponse(AuditFieldsMixin):
    booking_id:         str
    client_id:          str | None
    first_name:         str
    last_name:          str
    full_name:          str = ""
    date_of_birth:      date | None
    nationality:        str | None
    passport_number:    str | None
    passport_expiry:    date | None
    is_lead_passenger:  bool
    seat_preference:    str | None
    meal_preference:    str | None
    special_assistance: str | None