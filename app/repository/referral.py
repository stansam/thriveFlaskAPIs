
from app.models import Referral
from app.enums import ReferralStatus
from sqlalchemy import select as _select
from app.repository.base import BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)


class ReferralRepository(BaseRepository[Referral]):
    model = Referral

    def find_by_referrer(self, referrer_id: str) -> list[Referral]:
        stmt = (
            _select(Referral)
            .where(Referral.referrer_id == referrer_id)
            .order_by(Referral.created_at.desc())
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_by_referee(self, referee_id: str) -> Referral | None:
        stmt = _select(Referral).where(Referral.referee_id == referee_id)
        return self._session.execute(stmt).scalar_one_or_none()

    def find_pending(self) -> list[Referral]:
        stmt = _select(Referral).where(Referral.status == ReferralStatus.PENDING)
        return list(self._session.execute(stmt).scalars().all())

    def qualify(
        self,
        referral: Referral,
        qualifying_booking_id: str,
        actor_id: str | None = None,
    ) -> Referral:
        return self.update(
            referral,
            actor_id=actor_id,
            status=ReferralStatus.QUALIFIED,
            qualifying_booking_id=qualifying_booking_id,
        )

    def credit(self, referral: Referral, actor_id: str | None = None) -> Referral:
        return self.update(referral, actor_id=actor_id, status=ReferralStatus.CREDITED)

