# services/referral_service.py
"""
ReferralService — client referral tracking and qualification.

Implements interfaces.md § 10. ReferralService.
"""

from __future__ import annotations

from decimal import Decimal

from app.models.base import db
from app.enums import AuditActionType, ReferralStatus
from app.core.errors.handlers import BadRequestError, ConflictError, NotFoundError
from app.core.events import event_bus
from app.core.events.dataclass import ReferralQualifiedEvent
from app.dto import ReferralCreateRequest, ReferralResponse
from app.repository import referral_repo, client_repo, booking_repo
from app.interface._base import BaseService
from app.core.logging import get_logger
from app.core.dependencies import get_services
logger = get_logger(__name__)


class ReferralService(BaseService):

    def create_referral(
        self, referrer_id: str, referee_id: str, actor_id: str
    ) -> ReferralResponse:
        if referrer_id == referee_id:
            raise BadRequestError("A client cannot refer themselves.")

        client_repo.get_or_404(referrer_id)
        client_repo.get_or_404(referee_id)

        existing = referral_repo.find_by_referee(referee_id)
        if existing:
            raise ConflictError(
                f"Client {referee_id} has already been referred "
                f"(referral id={existing.id})."
            )

        referral = referral_repo.create(
            actor_id=actor_id,
            referrer_id=referrer_id,
            referee_id=referee_id,
            status=ReferralStatus.PENDING,
            credit_usd=Decimal("10.00"),
        )
        self._audit(
            AuditActionType.CREATE, actor_id, "referral", referral.id,
            description=f"Referral created: {referrer_id} → {referee_id}.",
        )
        db.session.commit()
        return _enrich(referral)

    def check_and_qualify(self, booking_id: str, actor_id: str) -> None:
        """
        Called when a booking reaches CONFIRMED status.
        If the booking's client has a PENDING referral, qualify + credit it.
        """
        booking = booking_repo.get(booking_id)
        if not booking:
            return

        referral = referral_repo.find_by_referee(booking.client_id)
        if not referral or referral.status != ReferralStatus.PENDING:
            return

        referral_repo.qualify(referral, qualifying_booking_id=booking_id, actor_id=actor_id)

        get_services().loyalty.credit_referral(referral.id, actor_id=actor_id)

        self._audit(
            AuditActionType.UPDATE, actor_id, "referral", referral.id,
            description=f"Referral qualified by booking {booking_id}.",
        )
        db.session.commit()

        event_bus.publish(ReferralQualifiedEvent(
            referral_id=referral.id,
            referrer_id=referral.referrer_id,
            referee_id=referral.referee_id,
            credit_usd=str(referral.credit_usd),
        ))

    def get_referral(self, referral_id: str) -> ReferralResponse:
        referral = referral_repo.get_or_404(referral_id)
        return _enrich(referral)

    def list_referrals_by_referrer(self, referrer_id: str) -> list[ReferralResponse]:
        client_repo.get_or_404(referrer_id)
        referrals = referral_repo.find_by_referrer(referrer_id)
        return [_enrich(r) for r in referrals]

    def list_pending_referrals(self) -> list[ReferralResponse]:
        return [_enrich(r) for r in referral_repo.find_pending()]


def _enrich(r) -> ReferralResponse:
    resp = ReferralResponse.model_validate(r)
    try:
        referrer = client_repo.get(r.referrer_id)
        referee  = client_repo.get(r.referee_id)
        resp.referrer_name = referrer.full_name if referrer else ""
        resp.referee_name  = referee.full_name if referee else ""
    except Exception:
        pass
    return resp


referral_service = ReferralService()