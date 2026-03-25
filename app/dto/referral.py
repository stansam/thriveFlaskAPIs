# dtos/referral.py
from __future__ import annotations
from decimal import Decimal
from typing import Annotated
from pydantic import Field
from app.enums import ReferralStatus
from .common import AuditFieldsMixin, StrictRequestModel

class ReferralCreateRequest(StrictRequestModel):
    referrer_id: str
    referee_id: str
    credit_usd: Annotated[Decimal, Field(default=Decimal("10.00"), gt=Decimal("0"))] = Decimal("10.00")

class ReferralResponse(AuditFieldsMixin):
    referrer_id: str
    referee_id: str
    status: ReferralStatus
    credit_usd: Decimal
    qualifying_booking_id: str | None
    referrer_name: str = ""
    referee_name: str = ""
