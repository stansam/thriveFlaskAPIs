"""
Separated Operations for ClientService.

Following CQRS and strict SRP, each client lifecycle action is a dedicated 
Operation class. They are all composed together by the ClientService facade.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from app.interface._base import BaseService
from app.enums import AuditActionType, BookingStatus, ClientType
from app.core.errors.handlers import (
    BadRequestError,
    DuplicateEmailError,
    NotFoundError,
)
from app.core.events import event_bus
from app.core.events.dataclass.client import (
    ClientCreatedEvent,
    ClientUpdatedEvent,
    ClientDeactivatedEvent,
    ClientPreferenceUpdatedEvent,
)
from app.dto import (
    ClientCreateRequest,
    ClientResponse,
    ClientSummaryResponse,
    ClientUpdateRequest,
    ClientPreferenceResponse,
    ClientPreferenceUpdateRequest,
    LoyaltyBalanceResponse,
    LoyaltyLedgerEntryResponse,
    BookingSummaryResponse,
)
from app.repository.client import ClientRepository
from app.repository.preference import ClientPreferenceRepository
from app.repository.booking import BookingRepository
from app.repository.loyalty import LoyaltyLedgerRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork
from app.repository.base import Page
from app.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)


def _booking_summary(b: Any) -> BookingSummaryResponse:
    from app.models import FlightBooking, HotelBooking, CarBooking, PackageBooking
    line = ""
    if isinstance(b, FlightBooking):
        line = f"{b.origin_iata}→{b.destination_iata} {b.departure_date}"
    elif isinstance(b, HotelBooking):
        line = f"{b.hotel_name} {b.check_in_date}"
    elif isinstance(b, CarBooking):
        line = f"{b.pickup_location} {b.pickup_datetime.date()}"
    elif isinstance(b, PackageBooking):
        line = f"Package {b.package_id[:8]} {b.travel_date}"

    return BookingSummaryResponse(
        id=b.id,
        reference_number=b.reference_number,
        service_type=b.service_type,
        status=b.status,
        client_id=b.client_id,
        is_emergency=b.is_emergency,
        is_group=b.is_group,
        total_service_fee_usd=b.total_service_fee_usd,
        discount_amount_usd=b.discount_amount_usd,
        created_at=b.created_at,
        confirmed_at=b.confirmed_at,
        summary_line=line,
    )


class _ClientOperation(BaseService):
    """Base dependencies and helpers for client operations."""

    def __init__(
        self,
        client_repo: ClientRepository,
        client_preference_repo: ClientPreferenceRepository,
        booking_repo: BookingRepository,
        loyalty_repo: LoyaltyLedgerRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        self._clients = client_repo
        self._client_prefs = client_preference_repo
        self._bookings = booking_repo
        self._loyalty = loyalty_repo
        self._audits = audit_service
        self._uow = uow


class GetClientOperation(_ClientOperation):
    def execute(self, client_id: str) -> ClientResponse:
        client = self._clients.get(client_id)
        if not client:
            raise NotFoundError("Client", client_id)
            
        balance = self._loyalty.balance_for_client(client_id)
        
        from sqlalchemy import select
        from app.models.booking import Booking
        booking_count = self._bookings.count(
            select(Booking).where(Booking.client_id == client_id)
        )
        
        resp = ClientResponse.model_validate(client)
        resp.loyalty_balance_usd = balance
        resp.total_bookings = booking_count
        resp.full_name = client.full_name
        return resp


class GetClientByEmailOperation(_ClientOperation):
    def execute(self, email: str, get_op: GetClientOperation) -> ClientResponse:
        client = self._clients.find_by_email(email.lower().strip())
        if not client:
            raise NotFoundError("Client", email)
        return get_op.execute(client.id)


class ListClientsOperation(_ClientOperation):
    def execute(
        self,
        client_type: ClientType | None = None,
        corporate_account_id: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict[str, Any]:
        result = self._clients.paginate_clients(
            client_type=client_type,
            corporate_account_id=corporate_account_id,
            is_active=is_active,
            search=search,
            page=page,
            per_page=per_page,
        )
        items = []
        for c in result.items:
            r = ClientResponse.model_validate(c)
            r.full_name = c.full_name
            items.append(r)
        return {"items": items, **self._page_meta(result)}


class SearchClientsOperation(_ClientOperation):
    def execute(self, query: str, limit: int = 10) -> list[ClientSummaryResponse]:
        result = self._clients.paginate_clients(search=query, page=1, per_page=min(limit, 20))
        return [
            ClientSummaryResponse(
                id=c.id,
                full_name=c.full_name,
                email=c.email,
                phone=c.phone,
                whatsapp_number=c.whatsapp_number,
                client_type=c.client_type,
            )
            for c in result.items
        ]


class GetBookingHistoryOperation(_ClientOperation):
    def execute(
        self,
        client_id: str,
        status: BookingStatus | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict[str, Any]:
        if not self._clients.exists(id=client_id):
            raise NotFoundError("Client", client_id)
            
        result = self._bookings.paginate_bookings(
            client_id=client_id,
            status=status,
            page=page,
            per_page=per_page,
        )
        items = [_booking_summary(b) for b in result.items]
        return {"items": items, **self._page_meta(result)}


class GetLoyaltyBalanceOperation(_ClientOperation):
    def execute(self, client_id: str) -> LoyaltyBalanceResponse:
        if not self._clients.exists(id=client_id):
            raise NotFoundError("Client", client_id)
            
        balance = self._loyalty.balance_for_client(client_id)
        entries = self._loyalty.find_by_client(client_id)

        total_earned = sum(
            (e.amount_usd for e in entries if e.amount_usd > 0), Decimal("0.00")
        )
        total_redeemed = sum(
            (abs(e.amount_usd) for e in entries if e.amount_usd < 0), Decimal("0.00")
        )
        return LoyaltyBalanceResponse(
            client_id=client_id,
            balance_usd=balance,
            total_earned_usd=total_earned,
            total_redeemed_usd=total_redeemed,
            entries=[LoyaltyLedgerEntryResponse.model_validate(e) for e in entries],
        )


class CreateClientOperation(_ClientOperation):
    def execute(
        self, 
        data: ClientCreateRequest, 
        actor_id: str, 
        get_op: GetClientOperation
    ) -> ClientResponse:
        email = data.email.lower().strip()
        if self._clients.find_by_email(email):
            raise DuplicateEmailError(email)

        if data.referred_by_id:
            if not self._clients.exists(id=data.referred_by_id):
                raise NotFoundError("Referrer Client", data.referred_by_id)

        payload = data.model_dump(exclude={"email"})
        client = self._clients.create(
            actor_id=actor_id,
            email=email,
            **payload,
        )

        self._client_prefs.get_or_create(client_id=client.id, actor_id=actor_id)

        self._audits.log(
            action=AuditActionType.CREATE,
            actor_id=actor_id,
            entity_type="client",
            entity_id=client.id,
            description=f"Client '{email}' created.",
            after=self._snapshot(client, ["id", "email", "client_type", "referred_by_id"]),
            strict=True,
        )
        self._uow.commit()

        event_bus.publish(ClientCreatedEvent(
            client_id=client.id,
            email=client.email,
            referred_by=client.referred_by_id,
        ))
        logger.info("Client created: %s (id=%s) by actor=%s", email, client.id, actor_id)
        
        return get_op.execute(client.id)


class UpdateClientOperation(_ClientOperation):
    def execute(
        self,
        client_id: str,
        data: ClientUpdateRequest,
        actor_id: str,
        get_op: GetClientOperation,
    ) -> ClientResponse:
        client = self._clients.get(client_id)
        if not client:
            raise NotFoundError("Client", client_id)
            
        before = self._snapshot(client)
        
        updates = data.model_dump(exclude_none=True)
        if updates:
            self._clients.update(client, actor_id=actor_id, **updates)
            
        self._audits.log(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="client",
            entity_id=client_id,
            description=f"Client '{client.email}' updated: {list(updates.keys())}.",
            before=before,
            after=self._snapshot(client),
            strict=True,
        )
        self._uow.commit()

        event_bus.publish(ClientUpdatedEvent(
            client_id=client.id,
            fields_changed=list(updates.keys())
        ))
        logger.info("Client updated: %s (id=%s) fields=%s by actor=%s", client.email, client.id, list(updates.keys()), actor_id)

        return get_op.execute(client_id)


class DeactivateClientOperation(_ClientOperation):
    def execute(
        self, 
        client_id: str, 
        actor_id: str,
        get_op: GetClientOperation,
    ) -> ClientResponse:
        client = self._clients.get(client_id)
        if not client:
            raise NotFoundError("Client", client_id)
            
        active_statuses = [
            BookingStatus.PENDING_PAYMENT,
            BookingStatus.PAYMENT_RECEIVED,
            BookingStatus.ON_HOLD,
            BookingStatus.CONFIRMED,
        ]
        for status in active_statuses:
            bookings = self._bookings.find_by_client(client_id, status=status)
            if bookings:
                logger.warning("Deactivation failed: Client %s has %d active bookings", client_id, len(bookings))
                raise BadRequestError(
                    f"Cannot deactivate client with {len(bookings)} active booking(s). "
                    f"Cancel or complete them first."
                )

        self._clients.update(client, actor_id=actor_id, is_active=False)
        self._audits.log(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="client",
            entity_id=client_id,
            description=f"Client '{client.email}' deactivated.",
            before={"is_active": True},
            after={"is_active": False},
            strict=True,
        )
        self._uow.commit()

        event_bus.publish(ClientDeactivatedEvent(client_id=client.id))
        logger.info("Client deactivated: %s (id=%s) by actor=%s", client.email, client.id, actor_id)
        return get_op.execute(client_id)


class GetClientPreferenceOperation(_ClientOperation):
    def execute(self, client_id: str) -> ClientPreferenceResponse:
        if not self._clients.exists(id=client_id):
            raise NotFoundError("Client", client_id)
            
        pref = self._client_prefs.get_or_create(client_id=client_id)
        self._uow.commit()
        return ClientPreferenceResponse.model_validate(pref)


class UpdateClientPreferenceOperation(_ClientOperation):
    def execute(
        self,
        client_id: str,
        data: ClientPreferenceUpdateRequest,
        actor_id: str,
    ) -> ClientPreferenceResponse:
        if not self._clients.exists(id=client_id):
            raise NotFoundError("Client", client_id)
            
        pref = self._client_prefs.get_or_create(
            client_id=client_id, actor_id=actor_id
        )
        
        updates = data.model_dump(exclude_none=True)
        if updates:
            self._client_prefs.update(pref, actor_id=actor_id, **updates)
            
        self._uow.commit()

        event_bus.publish(ClientPreferenceUpdatedEvent(client_id=client_id))
        return ClientPreferenceResponse.model_validate(pref)
