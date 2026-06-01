# app/interface/client/__init__.py
"""
ClientService Facade.

Composes separated CQRS-like operations to formulate
the complete ClientService boundary.
"""
from __future__ import annotations

from app.enums import BookingStatus, ClientType
from app.dto import (
    ClientCreateRequest,
    ClientResponse,
    ClientSummaryResponse,
    ClientUpdateRequest,
    ClientPreferenceResponse,
    ClientPreferenceUpdateRequest,
    LoyaltyBalanceResponse,
    BookingSummaryResponse,
)
from app.repository.client import ClientRepository
from app.repository.preference import ClientPreferenceRepository
from app.repository.booking import BookingRepository
from app.repository.loyalty import LoyaltyLedgerRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork

from app.interface.client.services import (
    GetBookingSummaryOperation,
    GetClientOperation,
    GetClientByEmailOperation,
    ListClientsOperation,
    SearchClientsOperation,
    GetBookingHistoryOperation,
    GetLoyaltyBalanceOperation,
    CreateClientOperation,
    UpdateClientOperation,
    DeactivateClientOperation,
    GetClientPreferenceOperation,
    UpdateClientPreferenceOperation,
)


class ClientService:
    """Service handling end-customer management.

    Responsibilities
    ----------------
    - CRUD operations for clients
    - Managing client preferences
    - Strictly logging all mutation state changes via AuditService
    - Properly isolating database interactions via structured IUnitOfWork

    Dependencies (injected via constructor)
    ----------------------------------------
    client_repo            : ClientRepository
    client_preference_repo : ClientPreferenceRepository
    booking_repo           : BookingRepository
    loyalty_repo           : LoyaltyLedgerRepository
    audit_service          : AuditService
    uow                    : IUnitOfWork
    """

    def __init__(
        self,
        client_repo: ClientRepository,
        client_preference_repo: ClientPreferenceRepository,
        booking_repo: BookingRepository,
        loyalty_repo: LoyaltyLedgerRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        self._get_op = GetClientOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._get_by_email_op = GetClientByEmailOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._list_op = ListClientsOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._search_op = SearchClientsOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._get_booking_summary_op = GetBookingSummaryOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._history_op = GetBookingHistoryOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._loyalty_op = GetLoyaltyBalanceOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._create_op = CreateClientOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._update_op = UpdateClientOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._deactivate_op = DeactivateClientOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._get_pref_op = GetClientPreferenceOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )
        self._update_pref_op = UpdateClientPreferenceOperation(
            client_repo, client_preference_repo, booking_repo, loyalty_repo, audit_service, uow
        )

    def get_client(self, client_id: str) -> ClientResponse:
        return self._get_op.execute(client_id)

    def get_booking_summary(self, booking_id: str) -> BookingSummaryResponse:
        return self._get_booking_summary_op.execute(booking_id)

    def get_client_by_email(self, email: str) -> ClientResponse:
        return self._get_by_email_op.execute(email, self._get_op)

    def list_clients(
        self,
        client_type: ClientType | None = None,
        corporate_account_id: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        return self._list_op.execute(client_type, corporate_account_id, is_active, search, page, per_page)

    def search_clients(self, query: str, limit: int = 10) -> list[ClientSummaryResponse]:
        return self._search_op.execute(query, limit)

    def get_booking_history(
        self,
        client_id: str,
        status: BookingStatus | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        return self._history_op.execute(client_id, status, page, per_page)

    def get_loyalty_balance(self, client_id: str) -> LoyaltyBalanceResponse:
        return self._loyalty_op.execute(client_id)

    def create_client(self, data: ClientCreateRequest, actor_id: str) -> ClientResponse:
        return self._create_op.execute(data, actor_id, self._get_op)

    def update_client(
        self,
        client_id: str,
        data: ClientUpdateRequest,
        actor_id: str,
    ) -> ClientResponse:
        return self._update_op.execute(client_id, data, actor_id, self._get_op)

    def deactivate_client(self, client_id: str, actor_id: str) -> ClientResponse:
        return self._deactivate_op.execute(client_id, actor_id, self._get_op)

    def get_client_preference(self, client_id: str) -> ClientPreferenceResponse:
        return self._get_pref_op.execute(client_id)

    def update_client_preference(
        self,
        client_id: str,
        data: ClientPreferenceUpdateRequest,
        actor_id: str,
    ) -> ClientPreferenceResponse:
        return self._update_pref_op.execute(client_id, data, actor_id)
