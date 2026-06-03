"""
Separated Operations for AuthService.

Following CQRS and single-responsibility principles, each use-case 
is encapsulated in its own operation class. They are all orchestrated 
by the AuthService facade.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

from flask_login import login_user, logout_user
from argon2 import PasswordHasher

from app.core.errors.handlers import (
    MFARequiredError,
    MFAInvalidError,
    AccountInactiveError,
    InvalidCredentialsError,
    NotFoundError,
    BusinessRuleViolationError,
    PasswordResetTokenInvalidError,
)
from app.core.events import event_bus
from app.core.events.dataclass import (
    UserLoggedInEvent, UserLoggedOutEvent, PasswordChangedEvent,
    PasswordResetRequestedEvent, PasswordResetCompletedEvent,
    MFADisabledEvent, MFAEnrolledEvent,
)
from app.core.logging import get_logger
from app.core.security import (
    hash_password,
    verify_password,
    password_needs_rehash,
    generate_totp_secret,
    get_totp_provisioning_uri,
    verify_totp,
    create_reset_token,
    verify_reset_token,
    generate_totp_qr_data_url,
)
from app.core.security.login_guard import (
    is_ip_locked,
    record_failed_attempt,
    clear_attempts,
)
from app.core.token_denylist import ITokenDenylist
from app.core.unit_of_work import IUnitOfWork
from app.core.auth_user import FlaskLoginUser
from app.core.config import settings
from app.dto import LoginRequest, PasswordChangeRequest, ForgotPasswordResponse, PasswordResetRequest
from app.dto.user import UserResponse, MFASetupResponse
from app.enums import AuditActionType
from app.repository.user import UserRepository
from app.interface.audit import AuditService

logger: logging.Logger = get_logger(__name__)


class _BaseAuthOperation:
    """Base dependencies for auth operations."""

    def __init__(
        self,
        user_repo: UserRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
        denylist: ITokenDenylist,
    ) -> None:
        self._users = user_repo
        self._audits = audit_service
        self._uow = uow
        self._denylist = denylist


class LoginOperation(_BaseAuthOperation):
    def execute(
        self,
        data: LoginRequest,
        ip_address: str = "",
        user_agent: str = "",
    ) -> UserResponse:
        # 1. IP-level lockout check (before any DB query)
        if is_ip_locked(ip_address):
            logger.warning("Login blocked: IP %s is currently locked.", ip_address)
            raise InvalidCredentialsError()

        user = self._users.find_by_email(data.email)
        check_hash = user.password_hash if user else PasswordHasher().hash("_dummy_")

        if not verify_password(data.password, check_hash) or user is None:
            logger.warning(
                "Failed login attempt for email '%s' from %s",
                data.email,
                ip_address,
            )
            # Record IP-level failure
            record_failed_attempt(ip_address)
            # Record account-level failure (only if user exists — don't inflate count for ghost emails)
            if user:
                self._increment_failed_attempts(user, ip_address)
            raise InvalidCredentialsError()

        # 2. Account lockout check (after credential verification)
        if user.is_locked:
            logger.warning(
                "Login blocked: account %s locked until %s", user.id, user.locked_until
            )
            raise AccountInactiveError("Account is temporarily locked due to repeated failed login attempts.")

        if not user.is_active:
            raise AccountInactiveError()

        if user.mfa_is_enrolled:
            if not data.totp_code:
                raise MFARequiredError()
            if user.mfa_secret is not None and not verify_totp(user.mfa_secret, data.totp_code):
                record_failed_attempt(ip_address)
                self._increment_failed_attempts(user, ip_address)
                raise MFAInvalidError()

        # 3. Successful login — clear counters
        clear_attempts(ip_address)
        with self._uow:
            user.failed_login_count = 0
            user.locked_until = None

            if password_needs_rehash(user.password_hash):
                user.password_hash = hash_password(data.password)
                logger.info("Re-hashed password for user %s (parameter upgrade).", user.id)

            user.last_login_at = datetime.now(timezone.utc)
            self._users.save(user)

            self._audits.log(
                actor_id=str(user.id),
                action=AuditActionType.LOGIN,
                entity_type="user",
                entity_id=str(user.id),
                description=f"User '{user.email}' logged in.",
                ip_address=ip_address,
                user_agent=user_agent,
                strict=True,
            )
            self._uow.commit()

        flask_user = FlaskLoginUser(user)
        login_user(flask_user, remember=False)

        event_bus.publish(UserLoggedInEvent(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        ))

        logger.info(
            "Successful login: user=%s role=%s ip=%s",
            user.id,
            user.role.value,
            ip_address,
        )
        return UserResponse.from_user(user)

    def _increment_failed_attempts(self, user, ip_address: str) -> None:
        """Increment failed login counter and apply lockout if threshold reached."""
        count = (user.failed_login_count or 0) + 1
        locked_until = None
        if count >= 20:
            locked_until = datetime.now(timezone.utc) + timedelta(hours=24)
        elif count >= 10:
            locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        elif count >= 5:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)

        with self._uow:
            user.failed_login_count = count
            user.locked_until = locked_until
            self._users.save(user)
            self._uow.commit()

        if locked_until:
            logger.warning(
                "Account %s locked until %s after %d failed attempts.", user.id, locked_until, count
            )


class LogoutOperation(_BaseAuthOperation):
    def execute(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))

        with self._uow:
            self._audits.log(
                action=AuditActionType.LOGOUT,
                actor_id=str(user.id),
                entity_type="user",
                entity_id=str(user.id),
                description=f"User '{user.email}' logged out.",
                ip_address=ip_address,
                user_agent=user_agent,
                strict=True,
            )
            self._uow.commit()
        logout_user()

        event_bus.publish(UserLoggedOutEvent(user_id=user.id))
        logger.info("User %s logged out.", user.id)


class ChangePasswordOperation(_BaseAuthOperation):
    def execute(
        self,
        user_id: str,
        data: PasswordChangeRequest,
        actor_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))

        if not verify_password(data.current_password, user.password_hash):
            raise InvalidCredentialsError("Current password incorrect.")

        if data.current_password == data.new_password:
            raise BusinessRuleViolationError("New password must be different.")

        with self._uow:
            before: dict[str, object] = {"password_hash": "[REDACTED]"}
            user.password_hash = hash_password(data.new_password)
            self._users.save(user, actor_id=actor_id)

            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="user",
                entity_id=str(user.id),
                description=f"Password changed for user '{user.email}'.",
                before=before,
                after={"password_hash": "[REDACTED]"},
                ip_address=ip_address,
                user_agent=user_agent,
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(PasswordChangedEvent(user_id=user.id))
        logger.info("Password changed for user %s.", user.id)


class RequestPasswordResetOperation(_BaseAuthOperation):
    def execute(
        self,
        email: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> ForgotPasswordResponse:
        user = self._users.find_by_email(email)
        if user and user.is_active:
            reset_token = create_reset_token(str(user.id))
            with self._uow:
                self._audits.log(
                    action=AuditActionType.UPDATE,
                    actor_id=None,
                    entity_type="user",
                    entity_id=str(user.id),
                    description=f"Password reset requested for '{user.email}'.",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    strict=True,
                )
                self._uow.commit()

            event_bus.publish(PasswordResetRequestedEvent(
                user_id=user.id,
                reset_token=reset_token,
                email=user.email,
            ))
            logger.info("Password reset requested for user %s.", user.id)
        else:
            logger.info(
                "Password reset requested for unknown/inactive email '%s' from %s.",
                email,
                ip_address,
            )

        return ForgotPasswordResponse()


class ResetPasswordOperation(_BaseAuthOperation):
    def execute(
        self,
        data: PasswordResetRequest,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        try:
            user_id = verify_reset_token(data.token)
        except Exception:
            raise PasswordResetTokenInvalidError()

        consumed = self._denylist.consume(
            data.token,
            ttl_seconds=settings.JWT_RESET_TOKEN_EXPIRES_SECONDS,
        )
        if not consumed:
            logger.warning(
                "Password reset token already consumed or invalid for user_id=%s from %s.",
                user_id,
                ip_address,
            )
            raise PasswordResetTokenInvalidError()

        with self._uow:
            user = self._users.get(user_id)
            if not user:
                raise PasswordResetTokenInvalidError()

            user.password_hash = hash_password(data.new_password)
            self._users.save(user)

            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=None,
                entity_type="user",
                entity_id=str(user.id),
                description=f"Password reset completed for '{user.email}'.",
                after={"password_hash": "[REDACTED]"},
                ip_address=ip_address,
                user_agent=user_agent,
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(PasswordResetCompletedEvent(user_id=user.id))
        logger.info("Password reset completed for user %s.", user.id)


class EnrollMFAOperation(_BaseAuthOperation):
    def execute(self, user_id: str, actor_id: str) -> MFASetupResponse:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))

        if user.mfa_is_enrolled:
            raise BusinessRuleViolationError("MFA is already enrolled.")

        provisional_secret = generate_totp_secret()
        with self._uow:
            user.mfa_secret = f"{provisional_secret}:pending"
            self._users.save(user, actor_id=actor_id)
            self._uow.commit()

        provisioning_uri = get_totp_provisioning_uri(provisional_secret, user.email)
        qr_data_url = generate_totp_qr_data_url(provisioning_uri)

        logger.info("MFA enrollment started for user %s.", user_id)
        return MFASetupResponse(
            provisioning_uri=provisioning_uri,
            qr_code_data_url=qr_data_url,
        )


class ConfirmMFAEnrollmentOperation(_BaseAuthOperation):
    def execute(
        self,
        user_id: str,
        totp_code: str,
        actor_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))

        if not user.mfa_is_pending:
            raise MFAInvalidError("MFA enrollment has not been started.")

        provisional_secret = user.mfa_secret.removesuffix(":pending") if user.mfa_secret else None
        if not provisional_secret or not verify_totp(provisional_secret, totp_code):
            raise MFAInvalidError()

        with self._uow:
            user.mfa_secret = provisional_secret
            self._users.save(user, actor_id=actor_id)

            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="user",
                entity_id=str(user.id),
                description=f"MFA enrollment confirmed for '{user.email}'.",
                ip_address=ip_address,
                user_agent=user_agent,
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(MFAEnrolledEvent(user_id=user.id))
        logger.info("MFA activated for user %s.", user_id)


class DisableMFAOperation(_BaseAuthOperation):
    def execute(
        self,
        user_id: str,
        totp_code: str,
        actor_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))

        if not user.mfa_is_enrolled:
            raise MFAInvalidError("MFA is not currently enrolled.")

        if not user.mfa_secret or not verify_totp(user.mfa_secret, totp_code):
            raise MFAInvalidError()

        with self._uow:
            user.mfa_secret = None
            self._users.save(user, actor_id=actor_id)

            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="user",
                entity_id=str(user.id),
                description=f"MFA disabled for '{user.email}'.",
                ip_address=ip_address,
                user_agent=user_agent,
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(MFADisabledEvent(user_id=user.id))
        logger.info("MFA disabled for user %s.", user_id)
