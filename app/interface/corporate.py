# services/corporate_service.py
"""
CorporateService — corporate account and subscription management.

Implements interfaces.md § 4. CorporateService.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from app.models.base import db
from app.enums import AuditActionType, SubscriptionTier
from app.core.errors.handlers import (
    NotFoundError,
    SubscriptionLimitError,
)
from app.core.events import event_bus
from app.core.events.dataclass import  SubscriptionRenewedEvent, SubscriptionLimitWarningEvent
from app.dto import (
    ClientResponse,
    CorporateAccountCreateRequest,
    CorporateAccountResponse,
    CorporateAccountUpdateRequest,
    CorporateSubscriptionCreateRequest,
    CorporateSubscriptionResponse,
    CorporateSubscriptionUpdateRequest,
)
from app.repository import (
    corporate_account_repo,
    corporate_subscription_repo,
    client_repo,
)
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)

# Monthly fees per tier (mirroring the business plan)
_TIER_FEES: dict[SubscriptionTier, Decimal] = {
    SubscriptionTier.BRONZE: Decimal("150.00"),
    SubscriptionTier.SILVER: Decimal("300.00"),
    SubscriptionTier.GOLD:   Decimal("500.00"),
}
_TIER_LIMITS: dict[SubscriptionTier, int | None] = {
    SubscriptionTier.BRONZE: 6,
    SubscriptionTier.SILVER: 15,
    SubscriptionTier.GOLD:   None,   # unlimited
}
_WARNING_THRESHOLD = 0.80   # fire warning at 80% usage


class CorporateService(BaseService):
    # Account queries
    def get_corporate_account(self, account_id: str) -> CorporateAccountResponse:
        account = corporate_account_repo.get_or_404(account_id)
        resp = CorporateAccountResponse.model_validate(account)
        resp.client_count = len(client_repo.find_by_corporate_account(account_id))
        if account.subscription:
            sub = account.subscription
            resp.subscription = _build_sub_response(sub)
        return resp

    def list_corporate_accounts(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        result = corporate_account_repo.paginate_accounts(
            search=search, is_active=is_active, page=page, per_page=per_page
        )
        items = [CorporateAccountResponse.model_validate(a) for a in result.items]
        return {"items": items, **self._page_meta(result)}

    def list_account_clients(
        self, account_id: str, page: int = 1, per_page: int = 25
    ) -> dict:
        corporate_account_repo.get_or_404(account_id)
        result = client_repo.paginate_clients(
            corporate_account_id=account_id, page=page, per_page=per_page
        )
        items = []
        for c in result.items:
            r = ClientResponse.model_validate(c)
            r.full_name = c.full_name
            items.append(r)
        return {"items": items, **self._page_meta(result)}
    # Account mutations
    def create_corporate_account(
        self, data: CorporateAccountCreateRequest, actor_id: str
    ) -> CorporateAccountResponse:
        account = corporate_account_repo.create(
            actor_id=actor_id,
            **data.model_dump(),
        )
        self._audit(
            action=AuditActionType.CREATE,
            actor_id=actor_id,
            entity_type="corporate_account",
            entity_id=account.id,
            description=f"Corporate account '{data.company_name}' created.",
            after=self._snapshot(account, ["id", "company_name", "billing_email"]),
        )
        db.session.commit()
        return self.get_corporate_account(account.id)

    def update_corporate_account(
        self, account_id: str, data: CorporateAccountUpdateRequest, actor_id: str
    ) -> CorporateAccountResponse:
        account = corporate_account_repo.get_or_404(account_id)
        before = self._snapshot(account)
        updates = data.model_dump(exclude_none=True)
        if updates:
            corporate_account_repo.update(account, actor_id=actor_id, **updates)
        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="corporate_account",
            entity_id=account_id,
            description=f"Corporate account '{account.company_name}' updated.",
            before=before,
            after=self._snapshot(account),
        )
        db.session.commit()
        return self.get_corporate_account(account_id)

    def deactivate_corporate_account(self, account_id: str, actor_id: str) -> None:
        account = corporate_account_repo.get_or_404(account_id)
        corporate_account_repo.update(account, actor_id=actor_id, is_active=False)
        if account.subscription and account.subscription.is_active:
            corporate_subscription_repo.update(
                account.subscription, actor_id=actor_id, is_active=False
            )
        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="corporate_account",
            entity_id=account_id,
            description=f"Corporate account '{account.company_name}' deactivated.",
        )
        db.session.commit()
    # Subscription mutations
    def create_subscription(
        self, data: CorporateSubscriptionCreateRequest, actor_id: str
    ) -> CorporateSubscriptionResponse:
        """
        Create an active subscription for an account.
        Deactivates any pre-existing subscription first.
        """
        corporate_account_repo.get_or_404(data.account_id)

        existing = corporate_subscription_repo.find_by_account(data.account_id)
        if existing and existing.is_active:
            corporate_subscription_repo.update(
                existing, actor_id=actor_id, is_active=False
            )

        limits = _TIER_LIMITS[data.tier]
        sub = corporate_subscription_repo.create(
            actor_id=actor_id,
            account_id=data.account_id,
            tier=data.tier,
            monthly_fee=data.monthly_fee,
            bookings_limit=limits,
            bookings_used=0,
            concierge_247=(data.tier == SubscriptionTier.GOLD),
            billing_cycle_start=data.billing_cycle_start,
            billing_cycle_end=data.billing_cycle_end,
            is_active=True,
        )
        self._audit(
            action=AuditActionType.CREATE,
            actor_id=actor_id,
            entity_type="corporate_subscription",
            entity_id=sub.id,
            description=(
                f"Subscription created: {data.tier.value} "
                f"for account {data.account_id}."
            ),
            after=self._snapshot(sub),
        )
        db.session.commit()
        return _build_sub_response(sub)

    def upgrade_subscription(
        self,
        account_id: str,
        new_tier: SubscriptionTier,
        actor_id: str,
    ) -> CorporateSubscriptionResponse:
        """
        Upgrade (or downgrade) the tier.
        Creates a new subscription with a fresh billing cycle.
        """
        account = corporate_account_repo.get_or_404(account_id)
        existing = corporate_subscription_repo.find_by_account(account_id)
        if existing:
            corporate_subscription_repo.update(
                existing, actor_id=actor_id, is_active=False
            )

        now = datetime.now(timezone.utc)
        sub = corporate_subscription_repo.create(
            actor_id=actor_id,
            account_id=account_id,
            tier=new_tier,
            monthly_fee=_TIER_FEES[new_tier],
            bookings_limit=_TIER_LIMITS[new_tier],
            bookings_used=0,
            concierge_247=(new_tier == SubscriptionTier.GOLD),
            billing_cycle_start=now,
            billing_cycle_end=now + relativedelta(months=1),
            is_active=True,
        )
        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="corporate_subscription",
            entity_id=sub.id,
            description=f"Subscription upgraded to {new_tier.value} for account {account_id}.",
        )
        db.session.commit()
        return _build_sub_response(sub)

    def renew_subscription(self, account_id: str, actor_id: str) -> CorporateSubscriptionResponse:
        sub = corporate_subscription_repo.find_by_account(account_id)
        if not sub or not sub.is_active:
            raise NotFoundError("Active subscription", account_id)

        new_start = sub.billing_cycle_end
        new_end   = new_start + relativedelta(months=1)
        corporate_subscription_repo.reset_billing_cycle(
            sub, new_start=new_start, new_end=new_end, actor_id=actor_id
        )
        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="corporate_subscription",
            entity_id=sub.id,
            description=f"Subscription renewed for account {account_id}.",
        )
        db.session.commit()

        event_bus.publish(SubscriptionRenewedEvent(
            account_id=account_id,
            subscription_id=sub.id,
            tier=sub.tier.value,
        ))
        return _build_sub_response(sub)
    # Booking allowance
    def check_booking_allowance(self, account_id: str) -> bool:
        sub = corporate_subscription_repo.find_by_account(account_id)
        if not sub or not sub.is_active:
            return True   # non-subscribed corporate clients are not capped
        if sub.is_at_limit():
            raise SubscriptionLimitError()
        return True

    def increment_booking_usage(self, account_id: str, actor_id: str) -> None:
        sub = corporate_subscription_repo.find_by_account(account_id)
        if not sub or not sub.is_active:
            return

        corporate_subscription_repo.increment_bookings_used(sub, actor_id=actor_id)
        db.session.commit()

        # Fire warning at 80% of the limit
        if sub.bookings_limit:
            usage_pct = sub.bookings_used / sub.bookings_limit
            if usage_pct >= _WARNING_THRESHOLD:
                event_bus.publish(SubscriptionLimitWarningEvent(
                    account_id=account_id,
                    subscription_id=sub.id,
                    bookings_used=sub.bookings_used,
                    bookings_limit=sub.bookings_limit,
                ))

# Helpers
def _build_sub_response(sub) -> CorporateSubscriptionResponse:
    remaining = None
    if sub.bookings_limit is not None:
        remaining = max(0, sub.bookings_limit - sub.bookings_used)
    resp = CorporateSubscriptionResponse.model_validate(sub)
    resp.is_at_limit = sub.is_at_limit()
    resp.bookings_remaining = remaining
    return resp


corporate_service = CorporateService()