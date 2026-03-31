# app/interface/user/services.py
"""
Separated Operations for UserService.

Following CQRS and strict SRP, each user lifecycle action is a dedicated 
Operation class. They are all composed together by the UserService facade.
"""
from __future__ import annotations

import logging
from typing import Any

from app.enums import AuditActionType, UserRole
from app.core.errors.handlers import (
    BadRequestError,
    DuplicateEmailError,
    NotFoundError,
)
from app.core.security import hash_password
from app.core.events import event_bus
from app.core.events.dataclass import (
    UserCreatedEvent,
    UserUpdatedEvent,
    UserDeactivatedEvent,
    UserReactivatedEvent,
    UserPreferenceUpdatedEvent,
)
from app.dto import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
    UserPreferenceResponse,
    UserPreferenceUpdateRequest,
)
from app.repository.user import UserRepository
from app.repository.preference import UserPreferenceRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork
from app.repository.base import Page

logger = logging.getLogger(__name__)


class _BaseUserOperation:
    """Base dependencies and helpers for user operations."""

    def __init__(
        self,
        user_repo: UserRepository,
        user_preference_repo: UserPreferenceRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        self._users = user_repo
        self._user_prefs = user_preference_repo
        self._audits = audit_service
        self._uow = uow

    @staticmethod
    def _snapshot(obj: Any, fields: list[str] | None = None) -> dict:
        """
        Build a JSON-safe dict from an ORM object for audit snapshots.
        Only includes scalar columns; skips relationships to avoid lazy loads.
        If `fields` is provided, only those fields are included.
        """
        if obj is None:
            return {}
        try:
            from sqlalchemy import inspect
            mapper = inspect(type(obj))
            col_names = [c.key for c in mapper.columns]
            if fields:
                col_names = [f for f in fields if f in col_names]
            return {
                k: getattr(obj, k, None)
                for k in col_names
                if not k.startswith("password")  # never snapshot passwords
            }
        except Exception:
            return {"id": getattr(obj, "id", None)}

    @staticmethod
    def _page_meta(page: Page) -> dict:
        """Return pagination metadata dict from a repository Page."""
        return {
            "total":       page.total,
            "page":        page.page,
            "per_page":    page.per_page,
            "total_pages": page.total_pages,
            "has_next":    page.has_next,
            "has_prev":    page.has_prev,
        }


class GetUserOperation(_BaseUserOperation):
    def execute(self, user_id: str) -> UserResponse:
        user = self._users.get_or_404(user_id)
        return UserResponse.from_user(user)


class GetUserByEmailOperation(_BaseUserOperation):
    def execute(self, email: str) -> UserResponse:
        user = self._users.find_by_email(email.lower().strip())
        if not user:
            raise NotFoundError("User", email)
        return UserResponse.from_user(user)


class ListUsersOperation(_BaseUserOperation):
    def execute(
        self,
        role: UserRole | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        result = self._users.paginate_users(
            role=role,
            is_active=is_active,
            search=search,
            page=page,
            per_page=per_page,
        )
        return {
            "items": [UserResponse.from_user(u) for u in result.items],
            **self._page_meta(result),
        }


class CreateUserOperation(_BaseUserOperation):
    def execute(self, data: UserCreateRequest, actor_id: str) -> UserResponse:
        email = data.email.lower().strip()
        if self._users.exists(email=email):
            raise DuplicateEmailError(email)

        user = self._users.create(
            actor_id=actor_id,
            email=email,
            full_name=data.full_name,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=True,
        )

        # Initialise preference row with defaults
        self._user_prefs.get_or_create(user_id=user.id, actor_id=actor_id)

        self._audits.log(
            action=AuditActionType.CREATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"User '{email}' created with role '{data.role.value}'.",
            after=self._snapshot(user, ["id", "email", "full_name", "role", "is_active"]),
            strict=True,
        )
        self._uow.commit()

        event_bus.publish(UserCreatedEvent(user_id=user.id, email=email, role=data.role.value))
        logger.info("User created: %s (id=%s) by actor=%s", email, user.id, actor_id)
        
        return UserResponse.from_user(user)


class UpdateUserOperation(_BaseUserOperation):
    def execute(
        self,
        user_id: str,
        data: UserUpdateRequest,
        actor_id: str,
    ) -> UserResponse:
        user = self._users.get_or_404(user_id)
        before = self._snapshot(user, ["full_name", "phone", "role", "is_active"])

        updates = data.model_dump(exclude_none=True)
        if updates:
            self._users.update(user, actor_id=actor_id, **updates)

        self._audits.log(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"User '{user.email}' updated: {list(updates.keys())}.",
            before=before,
            after=self._snapshot(user, ["full_name", "phone", "role", "is_active"]),
            strict=True,
        )
        self._uow.commit()

        event_bus.publish(UserUpdatedEvent(user_id=user.id))
        return UserResponse.from_user(user)


class DeactivateUserOperation(_BaseUserOperation):
    def execute(self, user_id: str, actor_id: str) -> UserResponse:
        user = self._users.get_or_404(user_id)

        if user.role == UserRole.SUPER_ADMIN:
            active_admins = self._users.find_active_by_role(UserRole.SUPER_ADMIN)
            if len(active_admins) <= 1:
                raise BadRequestError(
                    "Cannot deactivate the last active SUPER_ADMIN account."
                )

        before = self._snapshot(user, ["is_active"])
        self._users.update(user, actor_id=actor_id, is_active=False)

        self._audits.log(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"User '{user.email}' deactivated.",
            before=before,
            after={"is_active": False},
            strict=True,
        )
        self._uow.commit()

        event_bus.publish(UserDeactivatedEvent(user_id=user.id))
        return UserResponse.from_user(user)


class ReactivateUserOperation(_BaseUserOperation):
    def execute(self, user_id: str, actor_id: str) -> UserResponse:
        user = self._users.get_or_404(user_id)
        before = self._snapshot(user, ["is_active"])
        self._users.update(user, actor_id=actor_id, is_active=True)

        self._audits.log(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"User '{user.email}' reactivated.",
            before=before,
            after={"is_active": True},
            strict=True,
        )
        self._uow.commit()

        event_bus.publish(UserReactivatedEvent(user_id=user.id))
        return UserResponse.from_user(user)


class GetUserPreferenceOperation(_BaseUserOperation):
    def execute(self, user_id: str) -> UserPreferenceResponse:
        self._users.get_or_404(user_id)
        pref = self._user_prefs.get_or_create(user_id=user_id)
        self._uow.commit()   # commit the lazy-create if it happened
        return UserPreferenceResponse.model_validate(pref)


class UpdateUserPreferenceOperation(_BaseUserOperation):
    def execute(
        self,
        user_id: str,
        data: UserPreferenceUpdateRequest,
        actor_id: str,
    ) -> UserPreferenceResponse:
        self._users.get_or_404(user_id)
        pref = self._user_prefs.get_or_create(user_id=user_id, actor_id=actor_id)

        updates = data.model_dump(exclude_none=True)
        if updates:
            self._user_prefs.update(pref, actor_id=actor_id, **updates)

        self._uow.commit()

        event_bus.publish(UserPreferenceUpdatedEvent(user_id=user_id))
        return UserPreferenceResponse.model_validate(pref)
