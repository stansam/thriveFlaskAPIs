# dtos/booking.py
"""
Booking DTOs for all service types:
  Flight, Hotel, Car, Package + BookingPassenger.

Status transition requests are validated against the allowed
transition graph to prevent invalid state jumps at the DTO layer.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, model_validator

from app.enums import (
    BookingStatus, BookingServiceType,
)
from .common import StrictRequestModel, ResponseModel

# BOOKING STATUS TRANSITION
# Allowed forward transitions per status
_ALLOWED_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING_PAYMENT:  {BookingStatus.PAYMENT_RECEIVED, BookingStatus.CANCELLED, BookingStatus.ON_HOLD},
    BookingStatus.PAYMENT_RECEIVED: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.REFUNDED},
    BookingStatus.ON_HOLD:          {BookingStatus.PAYMENT_RECEIVED, BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED:        {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    BookingStatus.COMPLETED:        set(),
    BookingStatus.CANCELLED:        {BookingStatus.REFUNDED},
    BookingStatus.REFUNDED:         set(),
}

class BookingStatusTransitionRequest(StrictRequestModel):
    """PATCH /bookings/{id}/status — advance booking through its lifecycle."""
    new_status: BookingStatus
    reason:     Annotated[str | None, Field(default=None, max_length=500,
                    description="Required when cancelling or refunding.")]

    @model_validator(mode="after")
    def reason_required_for_cancellation(self) -> "BookingStatusTransitionRequest":
        if self.new_status in (BookingStatus.CANCELLED, BookingStatus.REFUNDED):
            if not self.reason:
                raise ValueError("A reason is required when cancelling or refunding.")
        return self

# BOOKING SUMMARY  (cross-type list view)
class BookingSummaryResponse(ResponseModel):
    """
    Lightweight cross-type booking row for the admin dashboard list.
    Avoids loading all sub-type join tables for every row.
    """
    id:                    str
    reference_number:      str
    service_type:          BookingServiceType
    status:                BookingStatus
    client_id:             str
    client_name:           str = ""
    is_emergency:          bool
    is_group:              bool
    total_service_fee_usd: Decimal
    discount_amount_usd:   Decimal
    created_at:            datetime
    confirmed_at:          datetime | None
    # Type-specific summary fields (populated from sub-type)
    summary_line:          str = Field(
        default="",
        description="e.g. 'JFK→DXB 2025-07-01' or 'Dubai Luxury Escape 2025-08-10'"
    )
