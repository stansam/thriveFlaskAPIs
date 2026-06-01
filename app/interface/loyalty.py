# services/loyalty_service.py
"""
LoyaltyService — client credit ledger management.

Implements interfaces.md § 11. LoyaltyService.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from app.models.base import db
from app.models.loyalty import LoyaltyLedger
from app.enums import AuditActionType, LoyaltyTransactionType
from app.core.errors.handlers import BadRequestError, NotFoundError
from app.core.events import event_bus
from app.core.events.dataclass import ReferralQualifiedEvent
from app.core.logging import get_logger
from app.dto import LoyaltyBalanceResponse, LoyaltyLedgerEntryResponse
from app.repository import client_repo, loyalty_repo, referral_repo, booking_repo
from app.interface._base import BaseService

logger = get_logger(__name__)


class LoyaltyService(BaseService):

    def get_balance(self, client_id: str) -> LoyaltyBalanceResponse:
        client_repo.get_or_404(client_id)
        balance = loyalty_repo.balance_for_client(client_id)
        entries = loyalty_repo.find_by_client(client_id)
        earned   = sum((e.amount_usd for e in entries if e.amount_usd > 0), Decimal("0.00"))
        redeemed = sum((abs(e.amount_usd) for e in entries if e.amount_usd < 0), Decimal("0.00"))
        return LoyaltyBalanceResponse(
            client_id=client_id,
            balance_usd=balance,
            total_earned_usd=earned,
            total_redeemed_usd=redeemed,
            entries=[LoyaltyLedgerEntryResponse.model_validate(e) for e in entries],
        )

    def credit_referral(self, referral_id: str, actor_id: str) -> LoyaltyLedgerEntryResponse:
        referral = referral_repo.get_or_404(referral_id)
        entry = loyalty_repo.credit(
            client_id=referral.referrer_id,
            amount=referral.credit_usd,
            tx_type=LoyaltyTransactionType.REFERRAL_CREDIT,
            description=f"Referral credit for introducing client {referral.referee_id}.",
            referral_id=referral_id,
            actor_id=actor_id,
        )
        referral_repo.credit(referral, actor_id=actor_id)
        self._audit(
            AuditActionType.CREATE, actor_id, "loyalty_ledger", entry.id,
            description=f"Referral credit ${referral.credit_usd} for client {referral.referrer_id}.",
        )
        db.session.commit()
        return LoyaltyLedgerEntryResponse.model_validate(entry)

    def redeem_credit(
        self,
        client_id: str,
        booking_id: str,
        amount: Decimal,
        actor_id: str,
    ) -> LoyaltyLedgerEntryResponse:
        client_repo.get_or_404(client_id)
        booking = booking_repo.get_or_404(booking_id)
        balance = loyalty_repo.balance_for_client(client_id)
        if amount > balance:
            raise BadRequestError(
                f"Insufficient loyalty balance. Available: ${balance}, requested: ${amount}."
            )
        entry = loyalty_repo.redeem(
            client_id=client_id, booking_id=booking_id,
            amount=amount, actor_id=actor_id,
        )
        # Apply discount to booking
        new_discount = booking.discount_amount_usd + amount
        booking_repo.update(booking, actor_id=actor_id, discount_amount_usd=new_discount)
        self._audit(
            AuditActionType.UPDATE, actor_id, "loyalty_ledger", entry.id,
            description=f"Credit ${amount} redeemed for booking {booking_id}.",
        )
        db.session.commit()
        return LoyaltyLedgerEntryResponse.model_validate(entry)

    def manual_credit(
        self, client_id: str, amount: Decimal, description: str, actor_id: str
    ) -> LoyaltyLedgerEntryResponse:
        client_repo.get_or_404(client_id)
        entry = loyalty_repo.credit(
            client_id=client_id, amount=amount,
            tx_type=LoyaltyTransactionType.MANUAL_CREDIT,
            description=description, actor_id=actor_id,
        )
        self._audit(AuditActionType.CREATE, actor_id, "loyalty_ledger", entry.id,
                    description=f"Manual credit ${amount} for client {client_id}: {description}.")
        db.session.commit()
        return LoyaltyLedgerEntryResponse.model_validate(entry)

    def manual_debit(
        self, client_id: str, amount: Decimal, description: str, actor_id: str
    ) -> LoyaltyLedgerEntryResponse:
        client_repo.get_or_404(client_id)
        balance = loyalty_repo.balance_for_client(client_id)
        if amount > balance:
            raise BadRequestError(
                f"Debit ${amount} would result in negative balance (current: ${balance})."
            )
        entry = loyalty_repo.credit(
            client_id=client_id, amount=-amount,
            tx_type=LoyaltyTransactionType.MANUAL_DEBIT,
            description=description, actor_id=actor_id,
        )
        self._audit(AuditActionType.CREATE, actor_id, "loyalty_ledger", entry.id,
                    description=f"Manual debit ${amount} for client {client_id}: {description}.")
        db.session.commit()
        return LoyaltyLedgerEntryResponse.model_validate(entry)

    def expire_stale_credits(self, as_of_date: date, actor_id: str) -> int:
        """
        Background job: expire credits past their `expires_at` date.
        Creates EXPIRY ledger entries for each affected credit.
        """
        from datetime import datetime, timezone
        now = datetime.combine(as_of_date, datetime.min.time(), tzinfo=timezone.utc)
        from sqlalchemy import select, and_
        stmt = (
            select(LoyaltyLedger)
            .where(
                LoyaltyLedger.amount_usd > 0,
                LoyaltyLedger.transaction_type.in_([
                    LoyaltyTransactionType.REFERRAL_CREDIT,
                    LoyaltyTransactionType.MANUAL_CREDIT,
                ]),
                LoyaltyLedger.expires_at.is_not(None),
                LoyaltyLedger.expires_at <= now,
            )
        )
        credits = list(db.session.execute(stmt).scalars().all())
        count = 0
        for credit in credits:
            loyalty_repo.credit(
                client_id=credit.client_id,
                amount=-credit.amount_usd,
                tx_type=LoyaltyTransactionType.EXPIRY,
                description=f"Expired credit from {credit.created_at.date()}.",
                actor_id=actor_id,
            )
            count += 1
        if count:
            db.session.commit()
            logger.info("Expired %d loyalty credits.", count)
        return count