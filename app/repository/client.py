# repositories/client_repository.py
"""
Repositories for Client, CorporateAccount, and CorporateSubscription.

ClientRepository is the primary entry point.
CorporateAccountRepository and CorporateSubscriptionRepository
are used by the corporate workflow service.
"""

from __future__ import annotations
from sqlalchemy import or_, select

from app.models import Client
from app.enums import ClientType
from app.repository.base import BaseRepository, Page

from app.core.logging import get_logger

logger = get_logger(__name__)


class ClientRepository(BaseRepository[Client]):
    model = Client

    def find_by_email(self, email: str) -> Client | None:
        stmt = select(Client).where(Client.email == email.lower().strip())
        return self._session.execute(stmt).scalar_one_or_none()

    def find_by_whatsapp(self, number: str) -> Client | None:
        stmt = select(Client).where(Client.whatsapp_number == number)
        return self._session.execute(stmt).scalar_one_or_none()

    def find_by_passport(self, passport_number: str) -> Client | None:
        stmt = select(Client).where(Client.passport_number == passport_number)
        return self._session.execute(stmt).scalar_one_or_none()

    def find_referrals_made(self, referrer_id: str) -> list[Client]:
        stmt = (
            select(Client)
            .where(Client.referred_by_id == referrer_id)
            .order_by(Client.created_at.desc())
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_by_corporate_account(self, account_id: str) -> list[Client]:
        stmt = (
            select(Client)
            .where(Client.corporate_account_id == account_id)
            .order_by(Client.last_name, Client.first_name)
        )
        return list(self._session.execute(stmt).scalars().all())

    def marketing_opt_in_list(self) -> list[Client]:
        """Return all active clients who have opted in to marketing."""
        from app.models import ClientPreference
        stmt = (
            select(Client)
            .join(ClientPreference, ClientPreference.client_id == Client.id)
            .where(
                Client.is_active.is_(True),
                ClientPreference.marketing_opt_in.is_(True),
            )
            .order_by(Client.last_name, Client.first_name)
        )
        return list(self._session.execute(stmt).scalars().all())

    def paginate_clients(
        self,
        client_type: ClientType | None = None,
        corporate_account_id: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[Client]:
        stmt = select(Client)
        if client_type is not None:
            stmt = stmt.where(Client.client_type == client_type)
        if corporate_account_id is not None:
            stmt = stmt.where(Client.corporate_account_id == corporate_account_id)
        if is_active is not None:
            stmt = stmt.where(Client.is_active.is_(is_active))
        if search:
            term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Client.first_name.ilike(term),
                    Client.last_name.ilike(term),
                    Client.email.ilike(term),
                    Client.phone.ilike(term),
                )
            )
        stmt = stmt.order_by(Client.last_name, Client.first_name)
        return self.paginate(stmt, page=page, per_page=per_page)