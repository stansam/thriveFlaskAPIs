# services/client_service.py
"""
ClientService — end-customer management.

Implements interfaces.md § 3. ClientService:
  create_client, get_client, get_client_by_email, list_clients,
  update_client, deactivate_client,
  get_client_preference, update_client_preference,
  get_booking_history, get_loyalty_balance, search_clients
"""

from __future__ import annotations

from decimal import Decimal

from app.models.base import db
from app.enums import AuditActionType, BookingStatus, ClientType
from app.models import Booking, Client
from app.core.errors.handlers import (
    BadRequestError,
    DuplicateEmailError,
    NotFoundError,
)
from app.core.events import event_bus, ClientCreatedEvent
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
from app.repository import (
    client_repo,
    client_preference_repo,
    booking_repo,
    loyalty_repo,
)
from app.repository.base import Page
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClientService(BaseService):
    # Read
    def get_client(self, client_id: str) -> ClientResponse:
        client = client_repo.get_or_404(client_id)
        balance = loyalty_repo.balance_for_client(client_id)
        booking_count = booking_repo.count(
            __import__("sqlalchemy").select(
                __import__("models.booking", fromlist=["Booking"]).Booking
            ).where(
                __import__("models.booking", fromlist=["Booking"]).Booking.client_id == client_id
            )
        )
        resp = ClientResponse.model_validate(client)
        resp.loyalty_balance_usd = balance
        resp.total_bookings = booking_count
        resp.full_name = client.full_name
        return resp

    def get_client_by_email(self, email: str) -> ClientResponse:
        client = client_repo.find_by_email(email.lower().strip())
        if not client:
            raise NotFoundError("Client", email)
        return self.get_client(client.id)

    def list_clients(
        self,
        client_type: ClientType | None = None,
        corporate_account_id: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        result = client_repo.paginate_clients(
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

    def search_clients(self, query: str, limit: int = 10) -> list[ClientSummaryResponse]:
        result = client_repo.paginate_clients(search=query, page=1, per_page=min(limit, 20))
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

    def get_booking_history(
        self,
        client_id: str,
        status: BookingStatus | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        client_repo.get_or_404(client_id)
        result = booking_repo.paginate_bookings(
            client_id=client_id,
            status=status,
            page=page,
            per_page=per_page,
        )
        items = [_booking_summary(b) for b in result.items]
        return {"items": items, **self._page_meta(result)}

    def get_loyalty_balance(self, client_id: str) -> LoyaltyBalanceResponse:
        client_repo.get_or_404(client_id)
        balance = loyalty_repo.balance_for_client(client_id)
        entries = loyalty_repo.find_by_client(client_id)

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
    # Mutations
    def create_client(self, data: ClientCreateRequest, actor_id: str) -> ClientResponse:
        """
        Create a new client.

        Rules
        -----
        - Email must be globally unique across all clients.
        - referred_by_id must reference an existing client.
        - ClientPreference is initialised with defaults (lazy-created).
        - CLIENT_WELCOME notification event is fired.
        """
        email = data.email.lower().strip()
        if client_repo.find_by_email(email):
            raise DuplicateEmailError(email)

        if data.referred_by_id:
            client_repo.get_or_404(data.referred_by_id)

        payload = data.model_dump(exclude={"email"})
        client = client_repo.create(
            actor_id=actor_id,
            email=email,
            **payload,
        )

        client_preference_repo.get_or_create(client_id=client.id, actor_id=actor_id)

        self._audit(
            action=AuditActionType.CREATE,
            actor_id=actor_id,
            entity_type="client",
            entity_id=client.id,
            description=f"Client '{email}' created.",
            after=self._snapshot(client, ["id", "email", "client_type", "referred_by_id"]),
        )
        db.session.commit()

        event_bus.publish(ClientCreatedEvent(
            client_id=client.id,
            email=client.email,
            referred_by=client.referred_by_id,
        ))
        logger.info("Client created: %s (id=%s)", email, client.id)
        return self.get_client(client.id)

    def update_client(
        self,
        client_id: str,
        data: ClientUpdateRequest,
        actor_id: str,
    ) -> ClientResponse:
        client = client_repo.get_or_404(client_id)
        before = self._snapshot(client)
        updates = data.model_dump(exclude_none=True)
        if updates:
            client_repo.update(client, actor_id=actor_id, **updates)
        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="client",
            entity_id=client_id,
            description=f"Client '{client.email}' updated: {list(updates.keys())}.",
            before=before,
            after=self._snapshot(client),
        )
        db.session.commit()
        return self.get_client(client_id)

    def deactivate_client(self, client_id: str, actor_id: str) -> ClientResponse:
        """
        Deactivate a client.
        Blocked if the client has any non-terminal bookings.
        """
        client = client_repo.get_or_404(client_id)
        active_statuses = [
            BookingStatus.PENDING_PAYMENT,
            BookingStatus.PAYMENT_RECEIVED,
            BookingStatus.ON_HOLD,
            BookingStatus.CONFIRMED,
        ]
        for status in active_statuses:
            bookings = booking_repo.find_by_client(client_id, status=status)
            if bookings:
                raise BadRequestError(
                    f"Cannot deactivate client with {len(bookings)} active booking(s). "
                    f"Cancel or complete them first."
                )

        client_repo.update(client, actor_id=actor_id, is_active=False)
        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="client",
            entity_id=client_id,
            description=f"Client '{client.email}' deactivated.",
            before={"is_active": True},
            after={"is_active": False},
        )
        db.session.commit()
        return self.get_client(client_id)
    # Preferences
    def get_client_preference(self, client_id: str) -> ClientPreferenceResponse:
        client_repo.get_or_404(client_id)
        pref = client_preference_repo.get_or_create(client_id=client_id)
        db.session.commit()
        return ClientPreferenceResponse.model_validate(pref)

    def update_client_preference(
        self,
        client_id: str,
        data: ClientPreferenceUpdateRequest,
        actor_id: str,
    ) -> ClientPreferenceResponse:
        client_repo.get_or_404(client_id)
        pref = client_preference_repo.get_or_create(
            client_id=client_id, actor_id=actor_id
        )
        updates = data.model_dump(exclude_none=True)
        if updates:
            client_preference_repo.update(pref, actor_id=actor_id, **updates)
        db.session.commit()
        return ClientPreferenceResponse.model_validate(pref)

# Helper
def _booking_summary(b) -> BookingSummaryResponse:
    from models.booking import FlightBooking, HotelBooking, CarBooking, PackageBooking
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


client_service = ClientService()