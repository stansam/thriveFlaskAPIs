# app/interface/corporate/services.py
"""
Corporate Service Operations.

Strict, single-responsibility CQRS-style classes encapsulating all
corporate account and subscription interactions. Employs rigorous UoW controls
and explicit Audit logging.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from dateutil.relativedelta import relativedelta

from app.enums import AuditActionType, SubscriptionTier
from app.core.errors.handlers import (
    NotFoundError,
    SubscriptionLimitError,
)
from app.core.events import event_bus
from app.core.events.dataclass.corporate import (
    CorporateAccountCreatedEvent,
    CorporateAccountUpdatedEvent,
    CorporateAccountDeactivatedEvent,
    SubscriptionCreatedEvent,
    SubscriptionUpgradedEvent,
    SubscriptionRenewedEvent,
    SubscriptionLimitWarningEvent,
)
from app.dto import (
    ClientResponse,
    CorporateAccountCreateRequest,
    CorporateAccountResponse,
    CorporateAccountUpdateRequest,
    CorporateSubscriptionCreateRequest,
    CorporateSubscriptionResponse,
    CorporateSubscriptionUpdateRequest,
)
from app.interface._base import BaseService
from app.core.logging import get_logger


logger: logging.Logger = get_logger(__name__)

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


def _build_sub_response(sub: Any) -> CorporateSubscriptionResponse:
    remaining = None
    if sub.bookings_limit is not None:
        remaining = max(0, sub.bookings_limit - sub.bookings_used)
    resp = CorporateSubscriptionResponse.model_validate(sub)
    resp.is_at_limit = sub.is_at_limit()
    resp.bookings_remaining = remaining
    return resp


class _CorporateOperation(BaseService):
    """
    Base operation configuring injection boundaries.
    Provides standard audit mechanisms enforcing strict safety.
    """
    def __init__(
        self,
        corporate_account_repo: Any,
        corporate_subscription_repo: Any,
        client_repo: Any,
        audit_service: Any,
        uow: Any,
    ) -> None:
        self._accounts = corporate_account_repo
        self._subscriptions = corporate_subscription_repo
        self._clients = client_repo
        self._audits = audit_service
        self._uow = uow


class GetCorporateAccountOperation(_CorporateOperation):
    def execute(self, account_id: str) -> CorporateAccountResponse:
        account = self._accounts.get(account_id)
        if not account:
            raise NotFoundError("Corporate Account", account_id)
        resp = CorporateAccountResponse.model_validate(account)
        resp.client_count = len(self._clients.find_by_corporate_account(account_id))
        if account.subscription:
            resp.subscription = _build_sub_response(account.subscription)
        return resp


class ListCorporateAccountsOperation(_CorporateOperation):
    def execute(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict[str, Any]:
        result = self._accounts.paginate_accounts(
            search=search, is_active=is_active, page=page, per_page=per_page
        )
        items = [CorporateAccountResponse.model_validate(a) for a in result.items]
        return {"items": items, **self._page_meta(result)}


class ListAccountClientsOperation(_CorporateOperation):
    def execute(self, account_id: str, page: int = 1, per_page: int = 25) -> dict[str, Any]:
        if not self._accounts.exists(id=account_id):
            raise NotFoundError("Corporate Account", account_id)
            
        result = self._clients.paginate_clients(
            corporate_account_id=account_id, page=page, per_page=per_page
        )
        items = []
        for c in result.items:
            r = ClientResponse.model_validate(c)
            r.full_name = c.full_name
            items.append(r)
        return {"items": items, **self._page_meta(result)}


class CreateCorporateAccountOperation(_CorporateOperation):
    def execute(
        self, data: CorporateAccountCreateRequest, actor_id: str, get_op: GetCorporateAccountOperation
    ) -> CorporateAccountResponse:
        with self._uow:
            account = self._accounts.create(
                actor_id=actor_id,
                **data.model_dump(),
            )
            
            self._audits.log(
                action=AuditActionType.CREATE,
                actor_id=actor_id,
                entity_type="corporate_account",
                entity_id=account.id,
                description=f"Corporate account '{data.company_name}' created.",
                after=self._snapshot(account, ["id", "company_name", "billing_email"]),
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(CorporateAccountCreatedEvent(
            account_id=account.id,
            company_name=account.company_name,
        ))
        logger.info("Corporate account created: %s (id=%s) by actor=%s", account.company_name, account.id, actor_id)
        
        return get_op.execute(account.id)


class UpdateCorporateAccountOperation(_CorporateOperation):
    def execute(
        self, account_id: str, data: CorporateAccountUpdateRequest, actor_id: str, get_op: GetCorporateAccountOperation
    ) -> CorporateAccountResponse:
        with self._uow:
            account = self._accounts.get(account_id)
            if not account:
                raise NotFoundError("Corporate Account", account_id)
            before = self._snapshot(account)
            updates = data.model_dump(exclude_none=True)
            
            if updates:
                self._accounts.update(account, actor_id=actor_id, **updates)
            
            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="corporate_account",
                entity_id=account.id,
                description=f"Corporate account '{account.company_name}' updated.",
                before=before,
                after=self._snapshot(account),
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(CorporateAccountUpdatedEvent(
            account_id=account.id,
        ))
        logger.info("Corporate account updated: %s (id=%s) fields=%s by actor=%s", account.company_name, account.id, list(updates.keys()), actor_id)
        
        return get_op.execute(account_id)


class DeactivateCorporateAccountOperation(_CorporateOperation):
    def execute(self, account_id: str, actor_id: str) -> None:
        with self._uow:
            account = self._accounts.get(account_id)
            if not account:
                raise NotFoundError("Corporate Account", account_id)
            self._accounts.update(account, actor_id=actor_id, is_active=False)
            
            if account.subscription and account.subscription.is_active:
                self._subscriptions.update(
                    account.subscription, actor_id=actor_id, is_active=False
                )
            
            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="corporate_account",
                entity_id=account.id,
                description=f"Corporate account '{account.company_name}' deactivated.",
                after=self._snapshot(account),
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(CorporateAccountDeactivatedEvent(
            account_id=account.id,
        ))
        logger.info("Corporate account deactivated: %s (id=%s) by actor=%s", account.company_name, account.id, actor_id)


class CreateSubscriptionOperation(_CorporateOperation):
    def execute(
        self, data: CorporateSubscriptionCreateRequest, actor_id: str
    ) -> CorporateSubscriptionResponse:
        with self._uow:
            if not self._accounts.exists(id=data.account_id):
                raise NotFoundError("Corporate Account", data.account_id)
            existing = self._subscriptions.find_by_account(data.account_id)
            
            if existing and existing.is_active:
                self._subscriptions.update(
                    existing, actor_id=actor_id, is_active=False
                )
    
            limits = _TIER_LIMITS[data.tier]
            sub = self._subscriptions.create(
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
            
            self._audits.log(
                action=AuditActionType.CREATE,
                actor_id=actor_id,
                entity_type="corporate_subscription",
                entity_id=sub.id,
                description=f"Subscription created: {data.tier.value} for account {data.account_id}.",
                after=self._snapshot(sub),
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(SubscriptionCreatedEvent(
            account_id=data.account_id,
            subscription_id=sub.id,
            tier=data.tier.value,
        ))
        logger.info("Subscription created: %s for account_id=%s (sub_id=%s) by actor=%s", data.tier.value, data.account_id, sub.id, actor_id)
        
        return _build_sub_response(sub)


class UpgradeSubscriptionOperation(_CorporateOperation):
    def execute(
        self, account_id: str, new_tier: SubscriptionTier, actor_id: str
    ) -> CorporateSubscriptionResponse:
        with self._uow:
            account = self._accounts.get(account_id)
            if not account:
                raise NotFoundError("Corporate Account", account_id)
            existing = self._subscriptions.find_by_account(account_id)
            
            if existing:
                self._subscriptions.update(
                    existing, actor_id=actor_id, is_active=False
                )
    
            now = datetime.now(timezone.utc)
            sub = self._subscriptions.create(
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
            
            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="corporate_subscription",
                entity_id=sub.id,
                description=f"Subscription upgraded to {new_tier.value} for account {account_id}.",
                after=self._snapshot(sub),
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(SubscriptionUpgradedEvent(
            account_id=account_id,
            subscription_id=sub.id,
            new_tier=new_tier.value,
        ))
        logger.info("Subscription upgraded: account_id=%s to tier=%s by actor=%s", account_id, new_tier.value, actor_id)
        
        return _build_sub_response(sub)


class RenewSubscriptionOperation(_CorporateOperation):
    def execute(self, account_id: str, actor_id: str) -> CorporateSubscriptionResponse:
        with self._uow:
            sub = self._subscriptions.find_by_account(account_id)
            if not sub or not sub.is_active:
                raise NotFoundError("Active subscription", account_id)
    
            new_start = sub.billing_cycle_end
            new_end   = new_start + relativedelta(months=1)
            self._subscriptions.reset_billing_cycle(
                sub, new_start=new_start, new_end=new_end, actor_id=actor_id
            )
            
            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="corporate_subscription",
                entity_id=sub.id,
                description=f"Subscription renewed for account {account_id}.",
                after=self._snapshot(sub),
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(SubscriptionRenewedEvent(
            account_id=account_id,
            subscription_id=sub.id,
            tier=sub.tier.value,
        ))
        logger.info("Subscription renewed: account_id=%s (id=%s) by actor=%s", account_id, sub.id, actor_id)
        
        return _build_sub_response(sub)


class CheckBookingAllowanceOperation(_CorporateOperation):
    def execute(self, account_id: str) -> bool:
        sub = self._subscriptions.find_by_account(account_id)
        if not sub or not sub.is_active:
            return True   # non-subscribed corporate clients are not capped
        if sub.is_at_limit():
            logger.warning("Subscription limit reached for account %s: %d/%d bookings used", account_id, sub.bookings_used, sub.bookings_limit)
            raise SubscriptionLimitError()
        return True


class IncrementBookingUsageOperation(_CorporateOperation):
    def execute(self, account_id: str, actor_id: str) -> None:
        with self._uow:
            sub = self._subscriptions.find_by_account(account_id)
            if not sub or not sub.is_active:
                return
    
            self._subscriptions.increment_bookings_used(sub, actor_id=actor_id)
            self._uow.commit()

        # Fire warning at 80% of the limit mapping checks after the commit to prevent blocking.
        if sub.bookings_limit:
            usage_pct = sub.bookings_used / sub.bookings_limit
            if usage_pct >= _WARNING_THRESHOLD:
                event_bus.publish(SubscriptionLimitWarningEvent(
                    account_id=account_id,
                    subscription_id=sub.id,
                    bookings_used=sub.bookings_used,
                    bookings_limit=sub.bookings_limit,
                ))
                logger.warning("Subscription limit warning: account_id=%s reached %d/%d bookings", account_id, sub.bookings_used, sub.bookings_limit)
