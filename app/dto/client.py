# dtos/client.py
"""
Client, CorporateAccount, and CorporateSubscription DTOs.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import EmailStr, Field, field_validator

from app.enums import ClientType, SubscriptionTier
from .common import AuditFieldsMixin, StrictRequestModel, ResponseModel

# CLIENT
class ClientCreateRequest(StrictRequestModel):
    first_name: Annotated[str, Field(min_length=1, max_length=100)]
    last_name:  Annotated[str, Field(min_length=1, max_length=100)]
    email:      EmailStr
    phone:      Annotated[str | None, Field(default=None, max_length=30)]
    whatsapp_number: Annotated[str | None, Field(default=None, max_length=30)]
    nationality:     Annotated[str | None, Field(default=None, max_length=100)]
    passport_number: Annotated[str | None, Field(default=None, max_length=50)]
    passport_expiry: date | None = None
    date_of_birth:   date | None = None
    preferred_language: Annotated[str, Field(default="en", max_length=10)]
    client_type: ClientType = ClientType.INDIVIDUAL
    corporate_account_id: str | None = None
    referred_by_id:       str | None = None
    notes: Annotated[str | None, Field(default=None, max_length=2000)]

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("passport_expiry", "date_of_birth", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

class ClientUpdateRequest(StrictRequestModel):
    first_name:       str | None = None
    last_name:        str | None = None
    phone:            str | None = None
    whatsapp_number:  str | None = None
    nationality:      str | None = None
    passport_number:  str | None = None
    passport_expiry:  date | None = None
    date_of_birth:    date | None = None
    preferred_language: str | None = None
    client_type:      ClientType | None = None
    corporate_account_id: str | None = None
    is_active:        bool | None = None
    is_group_leader:  bool | None = None
    notes:            str | None = None

class ClientResponse(AuditFieldsMixin):
    first_name:       str
    last_name:        str
    email:            str
    phone:            str | None
    whatsapp_number:  str | None
    nationality:      str | None
    passport_expiry:  date | None
    date_of_birth:    date | None
    preferred_language: str
    client_type:      ClientType
    is_group_leader:  bool
    is_active:        bool
    corporate_account_id: str | None
    referred_by_id:   str | None
    notes:            str | None
    # Computed
    full_name:        str = ""
    loyalty_balance_usd: Decimal = Decimal("0.00")
    total_bookings:   int = 0

class ClientSummaryResponse(ResponseModel):
    """Lightweight client reference embedded in booking responses."""
    id: str
    full_name: str
    email: str
    phone: str | None
    whatsapp_number: str | None
    client_type: ClientType

