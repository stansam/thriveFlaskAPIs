# app/interface/user/services.py
"""
Separated Operations for UserService.

Following CQRS and strict SRP, each user lifecycle action is a dedicated 
Operation class. They are all composed together by the UserService facade.
"""
from __future__ import annotations

from typing import Any
import logging

from app.interface._base import BaseService
from app.dto import UserResponse, AdminUserResponse
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
    UserUpdateRequest,
    UserPreferenceResponse,
    UserPreferenceUpdateRequest,
    UserListResult,
)
from app.repository.user import UserRepository
from app.repository.preference import UserPreferenceRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork
from app.core.logging import get_logger

logger = get_logger(__name__)

class GetUserOperation:
    def __init__(self, user_repo: UserRepository) -> None:
        self._users = user_repo

    def execute(self, user_id: str, is_admin: bool = False) -> UserResponse | AdminUserResponse:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        if is_admin:
            return AdminUserResponse.from_user(user)
        return UserResponse.from_user(user)


class GetUserByEmailOperation:
    def __init__(self, user_repo: UserRepository) -> None:
        self._users = user_repo

    def execute(self, email: str, is_admin: bool = False) -> UserResponse | AdminUserResponse:
        user = self._users.find_by_email(email.lower().strip())
        if not user:
            raise NotFoundError("User", email)
        if is_admin:
            return AdminUserResponse.from_user(user)
        return UserResponse.from_user(user)


class ListUsersOperation:
    def __init__(self, user_repo: UserRepository) -> None:
        self._users = user_repo

    def execute(
        self,
        role: UserRole | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> UserListResult:
        result = self._users.paginate_users(
            role=role,
            is_active=is_active,
            search=search,
            page=page,
            per_page=per_page,
        )
        return UserListResult(
            items=[AdminUserResponse.from_user(u) for u in result.items],
            total=result.total,
            page=result.page,
            per_page=result.per_page,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )


class CreateUserOperation(BaseService):
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

    def execute(self, data: UserCreateRequest, actor_id: str) -> AdminUserResponse:
        email = data.email.lower().strip()
        if self._users.exists(email=email):
            raise DuplicateEmailError(email)

        with self._uow:
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

        event_bus.publish(
            UserCreatedEvent(
                user_id=user.id,
                email=email,
                role=data.role.value,
                full_name=data.full_name,
                actor_id=actor_id,
            )
        )
        logger.info("User created: %s (id=%s) by actor=%s", email, user.id, actor_id)
        
        return AdminUserResponse.from_user(user)


class UpdateUserOperation(BaseService):
    def __init__(
        self,
        user_repo: UserRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        self._users = user_repo
        self._audits = audit_service
        self._uow = uow

    def execute(
        self,
        user_id: str,
        data: UserUpdateRequest,
        actor_id: str,
        is_admin: bool = False,
    ) -> UserResponse | AdminUserResponse:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError("User", user_id)
            
        before = self._snapshot(user, ["full_name", "phone", "role", "is_active"])
        updates = data.model_dump(exclude_none=True)

        with self._uow:
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

        event_bus.publish(
            UserUpdatedEvent(
                user_id=user.id,
                changed_fields=list(updates.keys()),
                actor_id=actor_id,
            )
        )
        logger.info("User updated: %s (id=%s) fields=%s by actor=%s", user.email, user.id, list(updates.keys()), actor_id)
        if is_admin:
            return AdminUserResponse.from_user(user)
        return UserResponse.from_user(user)


class DeactivateUserOperation(BaseService):
    def __init__(
        self,
        user_repo: UserRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        self._users = user_repo
        self._audits = audit_service
        self._uow = uow

    def execute(self, user_id: str, actor_id: str) -> AdminUserResponse:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        if user.role == UserRole.SUPER_ADMIN:
            active_admins = self._users.find_active_by_role(UserRole.SUPER_ADMIN)
            if len(active_admins) <= 1:
                logger.error("Deactivation blocked: Attempt to deactivate the last SUPER_ADMIN (user_id=%s) by actor=%s", user_id, actor_id)
                raise BadRequestError(
                    "Cannot deactivate the last active SUPER_ADMIN account."
                )

        before = self._snapshot(user, ["is_active"])

        with self._uow:
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

        event_bus.publish(UserDeactivatedEvent(user_id=user.id, actor_id=actor_id))
        logger.info("User deactivated: %s (id=%s) by actor=%s", user.email, user.id, actor_id)
        return AdminUserResponse.from_user(user)


class ReactivateUserOperation(BaseService):
    def __init__(
        self,
        user_repo: UserRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        self._users = user_repo
        self._audits = audit_service
        self._uow = uow

    def execute(self, user_id: str, actor_id: str) -> AdminUserResponse:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        if user.is_active:
            logger.info(
                "Reactivate no-op: user %s (id=%s) is already active.",
                user.email,
                user_id,
            )
            return AdminUserResponse.from_user(user)
            
        before = self._snapshot(user, ["is_active"])

        with self._uow:
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

        event_bus.publish(UserReactivatedEvent(user_id=user.id, actor_id=actor_id))
        logger.info("User reactivated: %s (id=%s) by actor=%s", user.email, user.id, actor_id)
        return AdminUserResponse.from_user(user)


class GetUserPreferenceOperation:
    def __init__(
        self,
        user_repo: UserRepository,
        user_preference_repo: UserPreferenceRepository,
    ) -> None:
        self._users = user_repo
        self._user_prefs = user_preference_repo

    def execute(self, user_id: str) -> UserPreferenceResponse:
        if not self._users.exists(id=user_id):
            raise NotFoundError("User", user_id)
            
        pref = self._user_prefs.find_by_user(user_id)
        if pref is None:
            raise NotFoundError("UserPreference", user_id)
        return UserPreferenceResponse.model_validate(pref)


class UpdateUserPreferenceOperation(BaseService):
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

    def execute(
        self,
        user_id: str,
        data: UserPreferenceUpdateRequest,
        actor_id: str,
    ) -> UserPreferenceResponse:
        if not self._users.exists(id=user_id):
            raise NotFoundError("User", user_id)
            
        pref = self._user_prefs.get_or_create(user_id=user_id, actor_id=actor_id)
        before = self._snapshot(pref, list(data.__class__.model_fields.keys()))

        updates = data.model_dump(exclude_none=True)
        with self._uow:
            if updates:
                self._user_prefs.update(pref, actor_id=actor_id, **updates)
                self._audits.log(
                    action=AuditActionType.UPDATE,
                    actor_id=actor_id,
                    entity_type="user_preference",
                    entity_id=pref.id,
                    description=f"Preferences updated for user '{user_id}': {list(updates.keys())}.",
                    before=before,
                    after=self._snapshot(pref, list(updates.keys())),
                    strict=True,
                )
            self._uow.commit()

        event_bus.publish(
            UserPreferenceUpdatedEvent(
                user_id=user_id,
                changed_fields=list(updates.keys()),
                actor_id=actor_id,
            )
        )
        logger.info("User preferences updated: user_id=%s by actor=%s", user_id, actor_id)
        return UserPreferenceResponse.model_validate(pref)
