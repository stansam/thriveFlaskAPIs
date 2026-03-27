# dtos/payment.py
"""Payment DTOs."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from app.enums import PaymentStatus, PaymentMethod
from .common import AuditFieldsMixin, StrictRequestModel


class PaymentCreateRequest(StrictRequestModel):
    """POST /bookings/{id}/payments — log a new manual payment."""
    booking_id:   str
    amount_usd:   Annotated[Decimal, Field(gt=Decimal("0"))]
    currency:     Annotated[str, Field(default="USD", min_length=3, max_length=3)]
    exchange_rate: Annotated[Decimal | None, Field(default=None, gt=Decimal("0"))]
    method:       PaymentMethod
    reference:    Annotated[str | None, Field(default=None, max_length=200)]
    notes:        Annotated[str | None, Field(default=None, max_length=1000)]

    @field_validator("amount_usd", "exchange_rate", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        return Decimal(str(v)) if v is not None else v

    @field_validator("currency", mode="before")
    @classmethod
    def upper_currency(cls, v: str) -> str:
        return v.upper().strip()


class PaymentConfirmRequest(StrictRequestModel):
    """PATCH /payments/{id}/confirm — admin confirms receipt."""
    paid_at:           datetime | None = None
    payment_proof_url: Annotated[str | None, Field(default=None, max_length=2048)]
    notes:             Annotated[str | None, Field(default=None, max_length=1000)]


class PaymentUpdateRequest(StrictRequestModel):
    """PATCH /payments/{id} — general update before confirmation."""
    amount_usd:        Decimal | None = None
    method:            PaymentMethod | None = None
    reference:         str | None = None
    payment_proof_url: str | None = None
    notes:             str | None = None
    status:            PaymentStatus | None = None


class PaymentResponse(AuditFieldsMixin):
    booking_id:        str
    amount_usd:        Decimal
    currency:          str
    exchange_rate:     Decimal | None
    method:            PaymentMethod
    status:            PaymentStatus
    reference:         str | None
    payment_proof_url: str | None
    paid_at:           datetime | None
    notes:             str | None
