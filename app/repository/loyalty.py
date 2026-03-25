
from decimal import Decimal as _D
from sqlalchemy import func as _func, select as _lselect

from app.models import LoyaltyLedger 
from app.enums import LoyaltyTransactionType
from app.repository.base import BaseRepository

class LoyaltyLedgerRepository(BaseRepository[LoyaltyLedger]):
    model = LoyaltyLedger

    def balance_for_client(self, client_id: str) -> _D:
        """Compute current balance as SUM(amount_usd)."""
        stmt = (
            _lselect(_func.sum(LoyaltyLedger.amount_usd))
            .where(LoyaltyLedger.client_id == client_id)
        )
        result = self._session.execute(stmt).scalar_one_or_none()
        return result or _D("0.00")

    def find_by_client(self, client_id: str) -> list[LoyaltyLedger]:
        stmt = (
            _lselect(LoyaltyLedger)
            .where(LoyaltyLedger.client_id == client_id)
            .order_by(LoyaltyLedger.created_at.desc())
        )
        return list(self._session.execute(stmt).scalars().all())

    def credit(
        self,
        client_id: str,
        amount: _D,
        tx_type: LoyaltyTransactionType,
        description: str | None = None,
        booking_id: str | None = None,
        referral_id: str | None = None,
        actor_id: str | None = None,
    ) -> LoyaltyLedger:
        return self.create(
            actor_id=actor_id,
            client_id=client_id,
            amount_usd=amount,
            transaction_type=tx_type,
            description=description,
            booking_id=booking_id,
            referral_id=referral_id,
        )

    def redeem(
        self,
        client_id: str,
        amount: _D,
        booking_id: str,
        actor_id: str | None = None,
    ) -> LoyaltyLedger:
        return self.create(
            actor_id=actor_id,
            client_id=client_id,
            amount_usd=-abs(amount),
            transaction_type=LoyaltyTransactionType.BOOKING_DISCOUNT,
            description=f"Credit redeemed for booking",
            booking_id=booking_id,
        )