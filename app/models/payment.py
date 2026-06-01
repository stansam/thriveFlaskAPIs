from decimal import Decimal
from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import PaymentStatus, PaymentMethod

if TYPE_CHECKING:
    from app.models.booking import Booking

class Payment(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "payments"

    booking_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    exchange_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 6), nullable=True,
        doc="FX rate used for currency → USD conversion. NULL if USD.",
    )
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method_enum"), nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )
    reference: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        doc="External transaction ID (bank ref, M-Pesa code, PayPal ID, etc.).",
    )
    payment_proof_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True,
        doc="CDN URL of uploaded proof of payment screenshot.",
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        doc="Timestamp when admin confirmed receipt.",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="payments")

    def __repr__(self) -> str:
        return (
            f"<Payment ${self.amount_usd} [{self.method.value}/{self.status.value}] "
            f"booking={self.booking_id}>"
        )
