# repositories/payment_repository.py
"""Repository for Payment records."""

from __future__ import annotations

from decimal import Decimal
from sqlalchemy import func, select

from models import Payment, PaymentStatus, PaymentMethod
from .base import BaseRepository, Page


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    def find_by_booking(self, booking_id: str) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.booking_id == booking_id)
            .order_by(Payment.created_at.desc())
        )
        return list(self._session.execute(stmt).scalars().all())

    def total_confirmed_for_booking(self, booking_id: str) -> Decimal:
        stmt = (
            select(func.sum(Payment.amount_usd))
            .where(
                Payment.booking_id == booking_id,
                Payment.status.in_([
                    PaymentStatus.CONFIRMED,
                    PaymentStatus.PARTIALLY_REFUNDED,
                ]),
            )
        )
        return self._session.execute(stmt).scalar_one_or_none() or Decimal("0.00")

    def find_pending(self) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.status == PaymentStatus.PENDING)
            .order_by(Payment.created_at)
        )
        return list(self._session.execute(stmt).scalars().all())

    def paginate_payments(
        self,
        booking_id: str | None = None,
        status: PaymentStatus | None = None,
        method: PaymentMethod | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[Payment]:
        stmt = select(Payment)
        if booking_id:
            stmt = stmt.where(Payment.booking_id == booking_id)
        if status:
            stmt = stmt.where(Payment.status == status)
        if method:
            stmt = stmt.where(Payment.method == method)
        stmt = stmt.order_by(Payment.created_at.desc())
        return self.paginate(stmt, page=page, per_page=per_page)
