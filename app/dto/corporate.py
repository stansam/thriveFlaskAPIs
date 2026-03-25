"""
Corporate account and subscription DTOs.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import EmailStr, Field, field_validator

from app.enums import SubscriptionTier
from .common import AuditFieldsMixin, StrictRequestModel

# CORPORATE ACCOUNT
class CorporateAccountCreateRequest(StrictRequestModel):
    company_name:          Annotated[str, Field(min_length=2, max_length=300)]
    industry:              Annotated[str | None, Field(default=None, max_length=100)]
    billing_email:         EmailStr
    billing_address:       str | None = None
    tax_id:                Annotated[str | None, Field(default=None, max_length=50)]
    primary_contact_name:  Annotated[str | None, Field(default=None, max_length=200)]
    primary_contact_phone: Annotated[str | None, Field(default=None, max_length=30)]


class CorporateAccountUpdateRequest(StrictRequestModel):
    company_name:          str | None = None
    industry:              str | None = None
    billing_email:         EmailStr | None = None
    billing_address:       str | None = None
    tax_id:                str | None = None
    primary_contact_name:  str | None = None
    primary_contact_phone: str | None = None
    is_active:             bool | None = None


class CorporateAccountResponse(AuditFieldsMixin):
    company_name:          str
    industry:              str | None
    billing_email:         str
    billing_address:       str | None
    tax_id:                str | None
    primary_contact_name:  str | None
    primary_contact_phone: str | None
    is_active:             bool
    # Nested
    subscription: "CorporateSubscriptionResponse | None" = None
    client_count: int = 0

# CORPORATE SUBSCRIPTION
class CorporateSubscriptionCreateRequest(StrictRequestModel):
    account_id:           str
    tier:                 SubscriptionTier
    monthly_fee:          Annotated[Decimal, Field(gt=Decimal("0"))]
    billing_cycle_start:  datetime
    billing_cycle_end:    datetime

    @field_validator("monthly_fee", mode="before")
    @classmethod
    def coerce_decimal(cls, v) -> Decimal:
        return Decimal(str(v))


class CorporateSubscriptionUpdateRequest(StrictRequestModel):
    tier:                SubscriptionTier | None = None
    monthly_fee:         Decimal | None = None
    billing_cycle_start: datetime | None = None
    billing_cycle_end:   datetime | None = None
    is_active:           bool | None = None


class CorporateSubscriptionResponse(AuditFieldsMixin):
    account_id:          str
    tier:                SubscriptionTier
    monthly_fee:         Decimal
    bookings_limit:      int | None
    bookings_used:       int
    concierge_247:       bool
    billing_cycle_start: datetime
    billing_cycle_end:   datetime
    is_active:           bool
    # Computed helpers
    is_at_limit:         bool = False
    bookings_remaining:  int | None = None
