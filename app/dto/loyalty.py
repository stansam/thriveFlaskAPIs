# dtos/loyalty.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from app.enums import LoyaltyTransactionType
from .common import AuditFieldsMixin, ResponseModel

class LoyaltyLedgerEntryResponse(AuditFieldsMixin):
    client_id: str
    transaction_type: LoyaltyTransactionType
    amount_usd: Decimal
    description: str | None
    booking_id: str | None
    referral_id: str | None
    expires_at: datetime | None

class LoyaltyBalanceResponse(ResponseModel):
    client_id: str
    balance_usd: Decimal
    total_earned_usd: Decimal = Decimal("0.00")
    total_redeemed_usd: Decimal = Decimal("0.00")
    entries: list[LoyaltyLedgerEntryResponse] = []
