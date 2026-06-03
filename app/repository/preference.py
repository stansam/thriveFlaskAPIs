from app.models import UserPreference, ClientPreference
from sqlalchemy import select as _pselect
from sqlalchemy.exc import IntegrityError
from app.repository.base import BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)


class UserPreferenceRepository(BaseRepository[UserPreference]):
    model = UserPreference

    def find_by_user(self, user_id: str) -> UserPreference | None:
        return self.get_by(user_id=user_id)

    def get_or_create(self, user_id: str, actor_id: str | None = None) -> UserPreference:
        pref = self.find_by_user(user_id)
        if pref is not None:
            return pref
        try:
            pref = self.create(actor_id=actor_id, user_id=user_id)
            return pref
        except IntegrityError:
            self._session.rollback()
            pref = self.find_by_user(user_id)
            if pref is None:
                raise
            return pref


class ClientPreferenceRepository(BaseRepository[ClientPreference]):
    model = ClientPreference

    def find_by_client(self, client_id: str) -> ClientPreference | None:
        return self.get_by(client_id=client_id)

    def get_or_create(self, client_id: str, actor_id: str | None = None) -> ClientPreference:
        pref = self.find_by_client(client_id)
        if pref is not None:
            return pref
        try:
            pref = self.create(actor_id=actor_id, client_id=client_id)
            return pref
        except IntegrityError:
            self._session.rollback()
            pref = self.find_by_client(client_id)
            if pref is None:
                raise
            return pref

    def find_whatsapp_opted_in(self) -> list[ClientPreference]:
        from app.enums import PreferredChannel
        stmt = _pselect(ClientPreference).where(
            ClientPreference.preferred_channel == PreferredChannel.WHATSAPP,
            ClientPreference.marketing_opt_in.is_(True),
        )
        return list(self._session.execute(stmt).scalars().all())
