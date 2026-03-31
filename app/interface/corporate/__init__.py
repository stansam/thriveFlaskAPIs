# app/interface/corporate/__init__.py
"""
CorporateService Facade.

Composes separated CQRS-like operations formulating
the complete Corporate Service boundary natively.
"""

from __future__ import annotations

from typing import Any
from app.enums import SubscriptionTier
from app.dto import (
    CorporateAccountCreateRequest,
    CorporateAccountResponse,
    CorporateAccountUpdateRequest,
    CorporateSubscriptionCreateRequest,
    CorporateSubscriptionResponse,
    ClientResponse,
)
from app.interface.corporate.services import (
    GetCorporateAccountOperation,
    ListCorporateAccountsOperation,
    ListAccountClientsOperation,
    CreateCorporateAccountOperation,
    UpdateCorporateAccountOperation,
    DeactivateCorporateAccountOperation,
    CreateSubscriptionOperation,
    UpgradeSubscriptionOperation,
    RenewSubscriptionOperation,
    CheckBookingAllowanceOperation,
    IncrementBookingUsageOperation,
)
from app.repository.corporate import CorporateAccountRepository, CorporateSubscriptionRepository
from app.repository.client import ClientRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork


class CorporateService:
    """Service handling multi-tenant corporate accounts scaling.

    Responsibilities
    ----------------
    - CRUD integrations over root corporate umbrellas
    - Subscription billing cycles handling
    - Strictly routing mutations through underlying UoW contexts

    Dependencies
    ------------
    corporate_account_repo
    corporate_subscription_repo
    client_repo
    audit_service
    uow
    """

    def __init__(
        self,
        corporate_account_repo: CorporateAccountRepository,
        corporate_subscription_repo: CorporateSubscriptionRepository,
        client_repo: ClientRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        args = (corporate_account_repo, corporate_subscription_repo, client_repo, audit_service, uow)
        
        self._get_op = GetCorporateAccountOperation(*args)
        self._list_op = ListCorporateAccountsOperation(*args)
        self._list_clients_op = ListAccountClientsOperation(*args)
        self._create_op = CreateCorporateAccountOperation(*args)
        self._update_op = UpdateCorporateAccountOperation(*args)
        self._deactivate_op = DeactivateCorporateAccountOperation(*args)
        self._create_sub_op = CreateSubscriptionOperation(*args)
        self._upgrade_sub_op = UpgradeSubscriptionOperation(*args)
        self._renew_sub_op = RenewSubscriptionOperation(*args)
        self._check_allowance_op = CheckBookingAllowanceOperation(*args)
        self._increment_usage_op = IncrementBookingUsageOperation(*args)

    # Account Queries
    def get_corporate_account(self, account_id: str) -> CorporateAccountResponse:
        return self._get_op.execute(account_id)

    def list_corporate_accounts(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict[str, Any]:
        return self._list_op.execute(search, is_active, page, per_page)

    def list_account_clients(
        self, account_id: str, page: int = 1, per_page: int = 25
    ) -> dict[str, Any]:
        return self._list_clients_op.execute(account_id, page, per_page)

    # Account Mutations
    def create_corporate_account(
        self, data: CorporateAccountCreateRequest, actor_id: str
    ) -> CorporateAccountResponse:
        return self._create_op.execute(data, actor_id, self._get_op)

    def update_corporate_account(
        self, account_id: str, data: CorporateAccountUpdateRequest, actor_id: str
    ) -> CorporateAccountResponse:
        return self._update_op.execute(account_id, data, actor_id, self._get_op)

    def deactivate_corporate_account(self, account_id: str, actor_id: str) -> None:
        self._deactivate_op.execute(account_id, actor_id)

    # Subscription Mutations
    def create_subscription(
        self, data: CorporateSubscriptionCreateRequest, actor_id: str
    ) -> CorporateSubscriptionResponse:
        return self._create_sub_op.execute(data, actor_id)

    def upgrade_subscription(
        self, account_id: str, new_tier: SubscriptionTier, actor_id: str
    ) -> CorporateSubscriptionResponse:
        return self._upgrade_sub_op.execute(account_id, new_tier, actor_id)

    def renew_subscription(self, account_id: str, actor_id: str) -> CorporateSubscriptionResponse:
        return self._renew_sub_op.execute(account_id, actor_id)

    # Booking Allowance
    def check_booking_allowance(self, account_id: str) -> bool:
        return self._check_allowance_op.execute(account_id)

    def increment_booking_usage(self, account_id: str, actor_id: str) -> None:
        self._increment_usage_op.execute(account_id, actor_id)
