# dtos/fee.py
"""Service fee schedule, fee line, and snapshot DTOs."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from app.enums import FeeType, BookingChannel
from .common import AuditFieldsMixin, StrictRequestModel

class ServiceFeeCreateRequest(StrictRequestModel):
    fee_type:           FeeType
    label:              Annotated[str, Field(min_length=2, max_length=200)]
    amount_usd:         Annotated[Decimal, Field(ge=Decimal("0"))]
    min_amount_usd:     Decimal | None = None
    max_amount_usd:     Decimal | None = None
    is_per_passenger:   bool = False
    is_percentage:      bool = False
    is_active:          bool = True

    @field_validator("amount_usd", "min_amount_usd", "max_amount_usd", mode="before")
    @classmethod
    def coerce(cls, v):
        return Decimal(str(v)) if v is not None else v

class ServiceFeeResponse(AuditFieldsMixin):
    schedule_id:        str
    fee_type:           FeeType
    label:              str
    amount_usd:         Decimal
    min_amount_usd:     Decimal | None
    max_amount_usd:     Decimal | None
    is_per_passenger:   bool
    is_percentage:      bool
    is_active:          bool

class ServiceFeeScheduleCreateRequest(StrictRequestModel):
    name:           Annotated[str, Field(min_length=2, max_length=200)]
    description:    str | None = None
    effective_from: date
    effective_to:   date | None = None
    is_active:      bool = False
    fees:           list[ServiceFeeCreateRequest] = []

class ServiceFeeScheduleResponse(AuditFieldsMixin):
    name:           str
    description:    str | None
    effective_from: date
    effective_to:   date | None
    is_active:      bool
    fees:           list[ServiceFeeResponse] = []

class ServiceFeeSnapshotResponse(AuditFieldsMixin):
    booking_id:                  str
    fee_id:                      str | None
    fee_type:                    FeeType
    fee_label:                   str
    base_amount_usd:             Decimal
    applied_amount_usd:          Decimal
    num_passengers:              int | None
    channel:                     BookingChannel
    emergency_surcharge_applied: bool
