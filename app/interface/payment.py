# services/payment_service.py
"""
PaymentService — manual payment recording and confirmation.

Implements interfaces.md § 8. PaymentService.
"""

from __future__ import annotations

from decimal import Decimal

from app.models.base import db
from app.enums import(
    AuditActionType, BookingStatus,
    PaymentStatus, AssetOwnerType, AssetType
)
from app.core.errors.handlers import BadRequestError, NotFoundError
from app.core.events import event_bus
from app.core.events.dataclass import PaymentReceivedEvent, PaymentRefundedEvent
from app.core.logging import get_logger
from app.core.dependencies import get_services
from app.dto import (
    PaymentConfirmRequest,
    PaymentCreateRequest,
    PaymentResponse,
    MediaAssetUploadRequest,
    PaymentUpdateRequest,
)
from app.repository import payment_repo, booking_repo
from app.interface._base import BaseService

logger = get_logger(__name__)


class PaymentService(BaseService):
    # Queries
    def get_payment(self, payment_id: str) -> PaymentResponse:
        payment = payment_repo.get_or_404(payment_id)
        return PaymentResponse.model_validate(payment)

    def list_payments_for_booking(self, booking_id: str) -> list[PaymentResponse]:
        booking_repo.get_or_404(booking_id)
        payments = payment_repo.find_by_booking(booking_id)
        return [PaymentResponse.model_validate(p) for p in payments]

    def get_outstanding_balance(self, booking_id: str) -> Decimal:
        booking = booking_repo.get_or_404(booking_id)
        paid = payment_repo.total_confirmed_for_booking(booking_id)
        return max(
            Decimal("0.00"),
            booking.total_service_fee_usd - booking.discount_amount_usd - paid,
        )

    def paginate_payments(
        self,
        booking_id: str | None = None,
        status: PaymentStatus | None = None,
        method=None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        result = payment_repo.paginate_payments(
            booking_id=booking_id, status=status, method=method,
            page=page, per_page=per_page,
        )
        return {
            "items": [PaymentResponse.model_validate(p) for p in result.items],
            **self._page_meta(result),
        }
    # Mutations
    def log_payment(
        self, data: PaymentCreateRequest, actor_id: str
    ) -> PaymentResponse:
        booking_repo.get_or_404(data.booking_id)
        amount_usd = data.amount_usd
        if data.currency != "USD" and data.exchange_rate:
            amount_usd = (amount_usd / data.exchange_rate).quantize(Decimal("0.01"))

        payment = payment_repo.create(
            actor_id=actor_id,
            booking_id=data.booking_id,
            amount_usd=amount_usd,
            currency=data.currency,
            exchange_rate=data.exchange_rate,
            method=data.method,
            status=PaymentStatus.PENDING,
            reference=data.reference,
            notes=data.notes,
        )
        self._audit(
            AuditActionType.CREATE, actor_id, "payment", payment.id,
            description=f"Payment ${amount_usd} ({data.method.value}) logged for booking {data.booking_id}.",
            after=self._snapshot(payment, ["id", "amount_usd", "method", "status"]),
        )
        db.session.commit()
        return PaymentResponse.model_validate(payment)

    def confirm_payment(
        self, payment_id: str, data: PaymentConfirmRequest, actor_id: str
    ) -> PaymentResponse:
        from datetime import datetime, timezone
        payment = payment_repo.get_or_404(payment_id)
        if payment.status == PaymentStatus.CONFIRMED:
            raise BadRequestError("Payment is already confirmed.")

        before = {"status": payment.status.value}
        payment_repo.update(
            payment, actor_id=actor_id,
            status=PaymentStatus.CONFIRMED,
            paid_at=data.paid_at or datetime.now(timezone.utc),
            payment_proof_url=data.payment_proof_url,
            notes=data.notes or payment.notes,
        )

        # Advance booking if now fully paid
        balance = self.get_outstanding_balance(payment.booking_id)
        booking = booking_repo.get(payment.booking_id)
        if booking and balance <= Decimal("0.00"):
            if booking.status == BookingStatus.PENDING_PAYMENT:
                booking_repo.update(
                    booking, actor_id=actor_id, status=BookingStatus.PAYMENT_RECEIVED
                )

        self._audit(
            AuditActionType.UPDATE, actor_id, "payment", payment_id,
            description=f"Payment ${payment.amount_usd} confirmed.",
            before=before, after={"status": PaymentStatus.CONFIRMED.value},
        )
        db.session.commit()

        event_bus.publish(PaymentReceivedEvent(
            payment_id=payment_id,
            booking_id=payment.booking_id,
            client_id=booking.client_id if booking else "",
            amount_usd=str(payment.amount_usd),
            method=payment.method.value,
            actor_id=actor_id,
        ))
        return PaymentResponse.model_validate(payment)

    def reject_payment(
        self, payment_id: str, reason: str, actor_id: str
    ) -> PaymentResponse:
        payment = payment_repo.get_or_404(payment_id)
        if payment.status not in (PaymentStatus.PENDING,):
            raise BadRequestError(
                f"Cannot reject payment in '{payment.status.value}' status."
            )
        payment_repo.update(
            payment, actor_id=actor_id,
            status=PaymentStatus.FAILED,
            notes=f"Rejected: {reason}",
        )
        self._audit(
            AuditActionType.UPDATE, actor_id, "payment", payment_id,
            description=f"Payment rejected: {reason}.",
        )
        db.session.commit()
        return PaymentResponse.model_validate(payment)

    def issue_refund(
        self,
        payment_id: str,
        refund_amount: Decimal,
        reason: str,
        actor_id: str,
    ) -> PaymentResponse:
        original = payment_repo.get_or_404(payment_id)
        if original.status != PaymentStatus.CONFIRMED:
            raise BadRequestError("Can only refund a confirmed payment.")
        if refund_amount > original.amount_usd:
            raise BadRequestError(
                f"Refund amount ${refund_amount} exceeds original ${original.amount_usd}."
            )

        refund = payment_repo.create(
            actor_id=actor_id,
            booking_id=original.booking_id,
            amount_usd=-refund_amount,
            currency=original.currency,
            method=original.method,
            status=PaymentStatus.REFUNDED,
            reference=f"REFUND-{original.id[:8]}",
            notes=reason,
        )

        is_full = refund_amount >= original.amount_usd
        if is_full:
            booking = booking_repo.get(original.booking_id)
            if booking:
                booking_repo.update(
                    booking, actor_id=actor_id, status=BookingStatus.REFUNDED
                )

        self._audit(
            AuditActionType.CREATE, actor_id, "payment", refund.id,
            description=f"Refund ${refund_amount} issued for payment {payment_id}: {reason}.",
        )
        db.session.commit()

        event_bus.publish(PaymentRefundedEvent(
            payment_id=refund.id,
            booking_id=original.booking_id,
            client_id="",
            refund_amount=str(refund_amount),
            reason=reason,
            actor_id=actor_id,
        ))
        return PaymentResponse.model_validate(refund)

    def upload_payment_proof(
        self, payment_id: str, file, actor_id: str
    ) -> PaymentResponse:
        """Upload proof via MediaService, attach URL to payment."""
        payment = payment_repo.get_or_404(payment_id)
        meta = MediaAssetUploadRequest(
            asset_type=AssetType.RECEIPT,
            owner_type=AssetOwnerType.PAYMENT,
            owner_id=payment_id,
            is_public=False,
        )
        asset = get_services().media.upload_asset(file, meta, actor_id)
        payment_repo.update(payment, actor_id=actor_id, payment_proof_url=asset.cdn_url)
        db.session.commit()
        return PaymentResponse.model_validate(payment)


payment_service = PaymentService()