"""
AuthService Facade.

Composes separated CQRS-like auth operations to formulate
the complete AuthService boundary.
"""
from __future__ import annotations

from app.dto import LoginRequest, PasswordChangeRequest, ForgotPasswordResponse, PasswordResetRequest
from app.dto.user import UserResponse, MFASetupResponse
from app.dto.auth import UserRegistrationRequest
from app.repository.user import UserRepository
from app.repository.preference import UserPreferenceRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork
from app.core.token_denylist import ITokenDenylist

from app.interface.auth.services import (
    LoginOperation,
    LogoutOperation,
    ChangePasswordOperation,
    RequestPasswordResetOperation,
    ResetPasswordOperation,
    EnrollMFAOperation,
    ConfirmMFAEnrollmentOperation,
    DisableMFAOperation,
    RegisterUserOperation,
    GoogleOAuthOperation,
)


class AuthService:
    """Service handling authentication flows and security management.

    Responsibilities
    ----------------
    - Login / logout with Flask-Login session management
    - Password change with current-password verification
    - HMAC-signed password-reset flow with Redis-backed single-use denylist
    - TOTP MFA enrollment, confirmation, and disablement
    - Immutable audit log writes for every state change
    - Domain event dispatch after successful operations

    Dependencies (injected via constructor)
    ----------------------------------------
    user_repo     : UserRepository
    user_preference_repo : UserPreferenceRepository
    audit_service : AuditService    — owns strict audit logging
    uow           : IUnitOfWork     — owns commit/rollback boundary
    denylist      : ITokenDenylist  — single-use reset token enforcement
    """

    def __init__(
        self,
        user_repo: UserRepository,
        user_preference_repo: UserPreferenceRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
        denylist: ITokenDenylist,
    ) -> None:
        # Initialize granular operations
        self._login_op = LoginOperation(user_repo, audit_service, uow, denylist)
        self._logout_op = LogoutOperation(user_repo, audit_service, uow, denylist)
        self._change_pw_op = ChangePasswordOperation(user_repo, audit_service, uow, denylist)
        self._request_reset_op = RequestPasswordResetOperation(user_repo, audit_service, uow, denylist)
        self._reset_pw_op = ResetPasswordOperation(user_repo, audit_service, uow, denylist)
        self._enroll_mfa_op = EnrollMFAOperation(user_repo, audit_service, uow, denylist)
        self._confirm_mfa_op = ConfirmMFAEnrollmentOperation(user_repo, audit_service, uow, denylist)
        self._disable_mfa_op = DisableMFAOperation(user_repo, audit_service, uow, denylist)
        self._register_user_op = RegisterUserOperation(user_repo, user_preference_repo, audit_service, uow)
        self._google_oauth_op = GoogleOAuthOperation(user_repo, user_preference_repo, audit_service, uow)

    def login(
        self,
        data: LoginRequest,
        ip_address: str = "",
        user_agent: str = "",
    ) -> UserResponse:
        return self._login_op.execute(data, ip_address, user_agent)

    def logout(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        self._logout_op.execute(user_id, ip_address, user_agent)

    def change_password(
        self,
        user_id: str,
        data: PasswordChangeRequest,
        actor_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        self._change_pw_op.execute(user_id, data, actor_id, ip_address, user_agent)

    def request_password_reset(
        self,
        email: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> ForgotPasswordResponse:
        return self._request_reset_op.execute(email, ip_address, user_agent)

    def reset_password(
        self,
        data: PasswordResetRequest,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        self._reset_pw_op.execute(data, ip_address, user_agent)

    def enroll_mfa(
        self,
        user_id: str,
        actor_id: str,
    ) -> MFASetupResponse:
        return self._enroll_mfa_op.execute(user_id, actor_id)

    def confirm_mfa_enrollment(
        self,
        user_id: str,
        totp_code: str,
        actor_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        self._confirm_mfa_op.execute(user_id, totp_code, actor_id, ip_address, user_agent)

    def disable_mfa(
        self,
        user_id: str,
        totp_code: str,
        actor_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        self._disable_mfa_op.execute(user_id, totp_code, actor_id, ip_address, user_agent)

    def register_user(
        self,
        data: UserRegistrationRequest,
        ip_address: str = "",
        user_agent: str = "",
    ) -> UserResponse:
        return self._register_user_op.execute(data, ip_address, user_agent)

    def verify_google_oauth(
        self,
        profile: dict,
        ip_address: str = "",
        user_agent: str = "",
    ) -> UserResponse:
        return self._google_oauth_op.execute(profile, ip_address, user_agent)
