# services/user_service.py
"""
UserService — platform operator (staff) management.

Implements interfaces.md § 2. UserService:
  create_user, get_user, get_user_by_email, list_users,
  update_user, deactivate_user, reactivate_user,
  get_preference, update_preference
"""

from __future__ import annotations

import logging

from app.models.base import db
from app.enums import AuditActionType, UserRole
from app.models import User
from app.core.errors.handlers import (
    BadRequestError,
    DuplicateEmailError,
    NotFoundError,
)
from app.core.security import hash_password
from app.dto import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
    UserPreferenceResponse,
    UserPreferenceUpdateRequest,
)
from app.repository import user_repo, user_preference_repo
from app.repository.base import Page
from app.interface._base import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService):
    # Queries
    def get_user(self, user_id: str) -> UserResponse:
        user = user_repo.get_or_404(user_id)
        return UserResponse.from_user(user)

    def get_user_by_email(self, email: str) -> UserResponse:
        user = user_repo.find_by_email(email.lower().strip())
        if not user:
            raise NotFoundError("User", email)
        return UserResponse.from_user(user)

    def list_users(
        self,
        role: UserRole | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        result = user_repo.paginate_users(
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
    # Mutations
    def create_user(self, data: UserCreateRequest, actor_id: str) -> UserResponse:
        """
        Create a new platform operator.

        Rules
        -----
        - Email must be globally unique.
        - Password is hashed with Argon2id before storage.
        - UserPreference row is initialised with defaults.
        - AuditLog CREATE is written.
        """
        email = data.email.lower().strip()
        if user_repo.exists(email=email):
            raise DuplicateEmailError(email)

        user = user_repo.create(
            actor_id=actor_id,
            email=email,
            full_name=data.full_name,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=True,
        )

        # Initialise preference row with defaults
        user_preference_repo.get_or_create(user_id=user.id, actor_id=actor_id)

        self._audit(
            action=AuditActionType.CREATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"User '{email}' created with role '{data.role.value}'.",
            after=self._snapshot(user, ["id", "email", "full_name", "role", "is_active"]),
        )
        db.session.commit()

        logger.info("User created: %s (id=%s) by actor=%s", email, user.id, actor_id)
        return UserResponse.from_user(user)

    def update_user(
        self,
        user_id: str,
        data: UserUpdateRequest,
        actor_id: str,
    ) -> UserResponse:
        user = user_repo.get_or_404(user_id)
        before = self._snapshot(user, ["full_name", "phone", "role", "is_active"])

        updates = data.model_dump(exclude_none=True)
        if updates:
            user_repo.update(user, actor_id=actor_id, **updates)

        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"User '{user.email}' updated: {list(updates.keys())}.",
            before=before,
            after=self._snapshot(user, ["full_name", "phone", "role", "is_active"]),
        )
        db.session.commit()
        return UserResponse.from_user(user)

    def deactivate_user(self, user_id: str, actor_id: str) -> UserResponse:
        """
        Deactivate a user.

        Raises BadRequestError if the target is the last active SUPER_ADMIN —
        prevents locking everyone out of the system.
        """
        user = user_repo.get_or_404(user_id)

        if user.role == UserRole.SUPER_ADMIN:
            active_admins = user_repo.find_active_by_role(UserRole.SUPER_ADMIN)
            if len(active_admins) <= 1:
                raise BadRequestError(
                    "Cannot deactivate the last active SUPER_ADMIN account."
                )

        before = self._snapshot(user, ["is_active"])
        user_repo.update(user, actor_id=actor_id, is_active=False)

        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"User '{user.email}' deactivated.",
            before=before,
            after={"is_active": False},
        )
        db.session.commit()
        return UserResponse.from_user(user)

    def reactivate_user(self, user_id: str, actor_id: str) -> UserResponse:
        user = user_repo.get_or_404(user_id)
        before = self._snapshot(user, ["is_active"])
        user_repo.update(user, actor_id=actor_id, is_active=True)

        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"User '{user.email}' reactivated.",
            before=before,
            after={"is_active": True},
        )
        db.session.commit()
        return UserResponse.from_user(user)
    # Preferences
    def get_preference(self, user_id: str) -> UserPreferenceResponse:
        user_repo.get_or_404(user_id)
        pref = user_preference_repo.get_or_create(user_id=user_id)
        db.session.commit()   # commit the lazy-create if it happened
        return UserPreferenceResponse.model_validate(pref)

    def update_preference(
        self,
        user_id: str,
        data: UserPreferenceUpdateRequest,
        actor_id: str,
    ) -> UserPreferenceResponse:
        user_repo.get_or_404(user_id)
        pref = user_preference_repo.get_or_create(user_id=user_id, actor_id=actor_id)

        updates = data.model_dump(exclude_none=True)
        if updates:
            user_preference_repo.update(pref, actor_id=actor_id, **updates)

        db.session.commit()
        return UserPreferenceResponse.model_validate(pref)


user_service = UserService()