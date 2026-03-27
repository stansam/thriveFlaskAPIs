# repositories/user_repository.py
"""Repository for User (platform operators / admin staff)."""

from __future__ import annotations

from sqlalchemy import select

from app.models import User
from app.enums import UserRole
from .base import BaseRepository, Page


class UserRepository(BaseRepository[User]):
    model = User

    def find_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        return self._session.execute(stmt).scalar_one_or_none()

    def find_active_by_role(self, role: UserRole) -> list[User]:
        stmt = (
            select(User)
            .where(User.role == role, User.is_active.is_(True))
            .order_by(User.full_name)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_all_active(self) -> list[User]:
        stmt = select(User).where(User.is_active.is_(True)).order_by(User.full_name)
        return list(self._session.execute(stmt).scalars().all())

    def deactivate(self, user: User, actor_id: str) -> User:
        return self.update(user, actor_id=actor_id, is_active=False)

    def paginate_users(
        self,
        role: UserRole | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[User]:
        stmt = select(User)
        if role is not None:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active.is_(is_active))
        if search:
            term = f"%{search.lower()}%"
            stmt = stmt.where(
                User.full_name.ilike(term) | User.email.ilike(term)
            )
        stmt = stmt.order_by(User.full_name)
        return self.paginate(stmt, page=page, per_page=per_page)
