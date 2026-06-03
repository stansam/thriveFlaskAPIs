# app/interface/user/__init__.py
"""
UserService Facade.

Composes separated CQRS-like operations to formulate
the complete UserService boundary.
"""
from __future__ import annotations

from app.enums import UserRole
from app.dto import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
    UserPreferenceResponse,
    UserPreferenceUpdateRequest,
    UserListResult,
)
from app.repository.user import UserRepository
from app.repository.preference import UserPreferenceRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork

from app.interface.user.services import (
    GetUserOperation,
    GetUserByEmailOperation,
    ListUsersOperation,
    CreateUserOperation,
    UpdateUserOperation,
    DeactivateUserOperation,
    ReactivateUserOperation,
    GetUserPreferenceOperation,
    UpdateUserPreferenceOperation,
)


class UserService:
    """Service handling platform operator (staff) management.

    Responsibilities
    ----------------
    - CRUD operations for users
    - Managing user preferences
    - Strictly logging all mutation state changes via AuditService
    - Properly isolating database interactions via structured IUnitOfWork

    Dependencies (injected via constructor)
    ----------------------------------------
    user_repo            : UserRepository
    user_preference_repo : UserPreferenceRepository
    audit_service        : AuditService    — owns strict audit logging
    uow                  : IUnitOfWork     — owns commit/rollback boundary
    """

    def __init__(
        self,
        user_repo: UserRepository,
        user_preference_repo: UserPreferenceRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        self._get_op = GetUserOperation(user_repo)
        self._get_by_email_op = GetUserByEmailOperation(user_repo)
        self._list_op = ListUsersOperation(user_repo)
        self._create_op = CreateUserOperation(user_repo, user_preference_repo, audit_service, uow)
        self._update_op = UpdateUserOperation(user_repo, audit_service, uow)
        self._deactivate_op = DeactivateUserOperation(user_repo, audit_service, uow)
        self._reactivate_op = ReactivateUserOperation(user_repo, audit_service, uow)
        self._get_pref_op = GetUserPreferenceOperation(user_repo, user_preference_repo)
        self._update_pref_op = UpdateUserPreferenceOperation(user_repo, user_preference_repo, audit_service, uow)

    def get_user(self, user_id: str) -> UserResponse:
        return self._get_op.execute(user_id)

    def get_user_by_email(self, email: str) -> UserResponse:
        return self._get_by_email_op.execute(email)

    def list_users(
        self,
        role: UserRole | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> UserListResult:
        return self._list_op.execute(role, is_active, search, page, per_page)

    def create_user(self, data: UserCreateRequest, actor_id: str) -> UserResponse:
        return self._create_op.execute(data, actor_id)

    def update_user(self, user_id: str, data: UserUpdateRequest, actor_id: str) -> UserResponse:
        return self._update_op.execute(user_id, data, actor_id)

    def deactivate_user(self, user_id: str, actor_id: str) -> UserResponse:
        return self._deactivate_op.execute(user_id, actor_id)

    def reactivate_user(self, user_id: str, actor_id: str) -> UserResponse:
        return self._reactivate_op.execute(user_id, actor_id)

    def get_preference(self, user_id: str) -> UserPreferenceResponse:
        return self._get_pref_op.execute(user_id)

    def update_preference(
        self,
        user_id: str,
        data: UserPreferenceUpdateRequest,
        actor_id: str,
    ) -> UserPreferenceResponse:
        return self._update_pref_op.execute(user_id, data, actor_id)
