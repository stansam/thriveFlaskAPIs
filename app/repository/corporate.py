from __future__ import annotations
from datetime import datetime
from sqlalchemy import select

from app.models import CorporateAccount, CorporateSubscription, SubscriptionTier
from app.repository.base import BaseRepository, Page

class CorporateAccountRepository(BaseRepository[CorporateAccount]):
    model = CorporateAccount

    def find_by_company_name(self, name: str) -> list[CorporateAccount]:
        stmt = (
            select(CorporateAccount)
            .where(CorporateAccount.company_name.ilike(f"%{name}%"))
            .order_by(CorporateAccount.company_name)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_active(self) -> list[CorporateAccount]:
        stmt = (
            select(CorporateAccount)
            .where(CorporateAccount.is_active.is_(True))
            .order_by(CorporateAccount.company_name)
        )
        return list(self._session.execute(stmt).scalars().all())

    def paginate_accounts(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[CorporateAccount]:
        stmt = select(CorporateAccount)
        if is_active is not None:
            stmt = stmt.where(CorporateAccount.is_active.is_(is_active))
        if search:
            term = f"%{search}%"
            stmt = stmt.where(CorporateAccount.company_name.ilike(term))
        stmt = stmt.order_by(CorporateAccount.company_name)
        return self.paginate(stmt, page=page, per_page=per_page)


# ---------------------------------------------------------------------------
# CorporateSubscriptionRepository
# ---------------------------------------------------------------------------

class CorporateSubscriptionRepository(BaseRepository[CorporateSubscription]):
    model = CorporateSubscription

    def find_by_account(self, account_id: str) -> CorporateSubscription | None:
        stmt = select(CorporateSubscription).where(
            CorporateSubscription.account_id == account_id
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def find_active_by_tier(self, tier: SubscriptionTier) -> list[CorporateSubscription]:
        stmt = (
            select(CorporateSubscription)
            .where(
                CorporateSubscription.tier == tier,
                CorporateSubscription.is_active.is_(True),
            )
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_expiring_before(self, cutoff: datetime) -> list[CorporateSubscription]:
        """Return active subscriptions whose billing cycle ends before `cutoff`."""
        stmt = (
            select(CorporateSubscription)
            .where(
                CorporateSubscription.is_active.is_(True),
                CorporateSubscription.billing_cycle_end <= cutoff,
            )
            .order_by(CorporateSubscription.billing_cycle_end)
        )
        return list(self._session.execute(stmt).scalars().all())

    def increment_bookings_used(
        self, subscription: CorporateSubscription, actor_id: str | None = None
    ) -> CorporateSubscription:
        subscription.bookings_used += 1
        return self.save(subscription, actor_id=actor_id)

    def reset_billing_cycle(
        self,
        subscription: CorporateSubscription,
        new_start: datetime,
        new_end: datetime,
        actor_id: str | None = None,
    ) -> CorporateSubscription:
        return self.update(
            subscription,
            actor_id=actor_id,
            bookings_used=0,
            billing_cycle_start=new_start,
            billing_cycle_end=new_end,
        )
