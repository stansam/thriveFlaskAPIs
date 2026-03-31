"""
Separated Operations for AuthService.

Following CQRS and single-responsibility principles, each use-case 
is encapsulated in its own operation class. They are all orchestrated 
by the AuthService facade.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

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
        user = self._users.find_by_email(data.email)
        check_hash = user.password_hash if user else PasswordHasher().hash("_dummy_")

        if not verify_password(data.password, check_hash) or user is None:
            logger.warning(
                "Failed login attempt for email '%s' from %s",
                data.email,
                ip_address,
            )
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountInactiveError()

        if user.mfa_secret and not user.mfa_secret.endswith(":pending"):
            if not data.totp_code:
                raise MFARequiredError()
            if not verify_totp(user.mfa_secret, data.totp_code):
                raise MFAInvalidError()

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

        if self._denylist.is_consumed(data.token):
            logger.warning(
                "Replayed password reset token for user_id=%s from %s.",
                user_id,
                ip_address,
            )
            raise PasswordResetTokenInvalidError()

        user = self._users.get(user_id)
        if not user:
            raise PasswordResetTokenInvalidError()

        user.password_hash = hash_password(data.new_password)
        self._users.save(user)

        consumed = self._denylist.consume(
            data.token,
            ttl_seconds=settings.JWT_RESET_TOKEN_EXPIRES_SECONDS,
        )
        if not consumed:
            logger.warning("Concurrent reset token use detected for user_id=%s.", user_id)
            self._uow.rollback()
            raise PasswordResetTokenInvalidError()

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

        if user.mfa_secret and not user.mfa_secret.endswith(":pending"):
            raise BusinessRuleViolationError("MFA is already enrolled.")

        provisional_secret = generate_totp_secret()
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

        if not user.mfa_secret or not user.mfa_secret.endswith(":pending"):
            raise MFAInvalidError("MFA enrollment has not been started.")

        provisional_secret = user.mfa_secret.removesuffix(":pending")
        if not verify_totp(provisional_secret, totp_code):
            raise MFAInvalidError()

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

        if not user.mfa_secret or user.mfa_secret.endswith(":pending"):
            raise MFAInvalidError("MFA is not currently enrolled.")

        if not verify_totp(user.mfa_secret, totp_code):
            raise MFAInvalidError()

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
