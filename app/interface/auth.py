"""
Authentication Service.

Provides domain operations for authentication, session management,
passwords, and MFA lifecycle. Uses flask-login for establishing sessions.
Orchestrates domain models, handles business logic, and logs audit events.

Transaction boundary: every write method commits via an injected
`IUnitOfWork`; the service never touches repository session internals.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Final

from flask_login import login_user, logout_user

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
from app.repository.audit import AuditLogRepository

logger: logging.Logger = get_logger(__name__)

# Pre-computed Argon2id hash used as a constant-time dummy when the
# requested email does not exist. Prevents timing-based user enumeration.
# Generated once: `from argon2 import PasswordHasher; PasswordHasher().hash("_dummy_")`
_DUMMY_HASH: Final[str] = (
    "$argon2id$v=19$m=65536,t=3,p=4"
    "$c29tZXNhbHRzb21lc2FsdA"
    "$Vf1zUYMDe1RrMEHhJFUTLx5WwC/4zJXX3gM8Bq7N8Ko"
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
    user_repo   : UserRepository
    audit_repo  : AuditLogRepository
    uow         : IUnitOfWork     — owns commit/rollback boundary
    denylist    : ITokenDenylist  — single-use reset token enforcement
    """

    def __init__(
        self,
        user_repo: UserRepository,
        audit_repo: AuditLogRepository,
        uow: IUnitOfWork,
        denylist: ITokenDenylist,
    ) -> None:
        self._users = user_repo
        self._audits = audit_repo
        self._uow = uow
        self._denylist = denylist

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _write_audit(
        self,
        action: AuditActionType,
        actor_id: str | None,
        entity_type: str,
        entity_id: str | None = None,
        description: str | None = None,
        before: dict[str, object] | None = None,
        after: dict[str, object] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Write an immutable audit log entry within the current session.

        Args:
            action: The audit action type enum value.
            actor_id: UUID string of the user performing the action, or None.
            entity_type: The resource type string (e.g. "user").
            entity_id: UUID string of the affected resource, or None.
            description: Human-readable summary of the event.
            before: Before-state snapshot (password fields must be redacted).
            after: After-state snapshot (password fields must be redacted).
            ip_address: Request originator IP, or None.
            user_agent: HTTP User-Agent string, or None.
        """
        self._audits.create(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            before_snapshot=json.dumps(before) if before else None,
            after_snapshot=json.dumps(after) if after else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # ------------------------------------------------------------------ #
    #  Public service methods                                              #
    # ------------------------------------------------------------------ #

    def login(
        self,
        data: LoginRequest,
        ip_address: str = "",
        user_agent: str = "",
    ) -> UserResponse:
        """Authenticate user, evaluate active status, manage MFA challenge,
        stamp last_login_at, establish session, and write audit log.

        Args:
            data: Validated login request containing email, password, and
                optional TOTP code.
            ip_address: Request originator IP address (for audit + logging).
            user_agent: HTTP User-Agent string (for audit).

        Returns:
            UserResponse DTO for the authenticated user (no credentials).

        Raises:
            InvalidCredentialsError: If email not found or password incorrect.
            AccountInactiveError: If the account has been deactivated.
            MFARequiredError: If MFA is enrolled but no TOTP code was provided.
            MFAInvalidError: If the provided TOTP code is invalid or expired.
        """
        user = self._users.find_by_email(data.email)

        # Always run verify_password regardless of whether user exists.
        # This guarantees a constant-time path that defeats timing-based
        # email enumeration attacks.
        check_hash = user.password_hash if user else _DUMMY_HASH

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
            logger.info(
                "Re-hashed password for user %s (parameter upgrade).", user.id
            )

        user.last_login_at = datetime.now(timezone.utc)
        self._users.save(user)

        self._write_audit(
            actor_id=str(user.id),
            action=AuditActionType.LOGIN,
            entity_type="user",
            entity_id=str(user.id),
            description=f"User '{user.email}' logged in.",
            ip_address=ip_address,
            user_agent=user_agent,
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

    def logout(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        """Log out the current user and write audit event.

        Args:
            user_id: UUID string of the user to log out.
            ip_address: Request originator IP (for audit).
            user_agent: HTTP User-Agent string (for audit).

        Raises:
            NotFoundError: If no user with the given ID exists.
        """
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))

        self._write_audit(
            action=AuditActionType.LOGOUT,
            actor_id=str(user.id),
            entity_type="user",
            entity_id=str(user.id),
            description=f"User '{user.email}' logged out.",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._uow.commit()
        logout_user()

        event_bus.publish(UserLoggedOutEvent(user_id=user.id))
        logger.info("User %s logged out.", user.id)

    def change_password(
        self,
        user_id: str,
        data: PasswordChangeRequest,
        actor_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        """Verify current password, enforce uniqueness, hash new, save, audit.

        Args:
            user_id: UUID string of the user changing their password.
            data: Validated request with current_password and new_password.
            actor_id: UUID string of the actor (same as user_id for self-service).
            ip_address: Request originator IP (for audit).
            user_agent: HTTP User-Agent string (for audit).

        Raises:
            NotFoundError: If no user with the given ID exists.
            InvalidCredentialsError: If current_password does not match.
            BusinessRuleViolationError: If new password is identical to current.
        """
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

        self._write_audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=str(user.id),
            description=f"Password changed for user '{user.email}'.",
            before=before,
            after={"password_hash": "[REDACTED]"},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._uow.commit()

        event_bus.publish(PasswordChangedEvent(user_id=user.id))
        logger.info("Password changed for user %s.", user.id)

    def request_password_reset(
        self,
        email: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> ForgotPasswordResponse:
        """Generate a time-limited HMAC-signed reset token and dispatch event.

        Always returns success to prevent email enumeration — the caller
        does not learn whether the email is registered.

        Args:
            email: The email address to send the reset link to.
            ip_address: Request originator IP (for audit).
            user_agent: HTTP User-Agent string (for audit).

        Returns:
            ForgotPasswordResponse with a generic success message.
        """
        user = self._users.find_by_email(email)
        if user and user.is_active:
            reset_token = create_reset_token(str(user.id))
            self._write_audit(
                action=AuditActionType.UPDATE,
                actor_id=None,
                entity_type="user",
                entity_id=str(user.id),
                description=f"Password reset requested for '{user.email}'.",
                ip_address=ip_address,
                user_agent=user_agent,
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

    def reset_password(
        self,
        data: PasswordResetRequest,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        """Validate HMAC token, enforce single-use via Redis, hash new password.

        Flow
        ----
        1. Verify HMAC signature + expiry via `verify_reset_token`.
        2. Check Redis denylist — reject if already consumed (replay).
        3. Load user; hash + persist new password.
        4. Mark token consumed in Redis (atomic SET-NX with TTL).
        5. Write audit log and dispatch domain event.

        Args:
            data: Validated request containing token and new_password.
            ip_address: Request originator IP (for audit).
            user_agent: HTTP User-Agent string (for audit).

        Raises:
            PasswordResetTokenInvalidError: If the token is malformed,
                expired, already used, or the user no longer exists.
        """
        # Step 1: verify HMAC signature + expiry
        try:
            user_id = verify_reset_token(data.token)
        except Exception:
            raise PasswordResetTokenInvalidError()

        # Step 2: reject replayed tokens before any DB work
        if self._denylist.is_consumed(data.token):
            logger.warning(
                "Replayed password reset token for user_id=%s from %s.",
                user_id,
                ip_address,
            )
            raise PasswordResetTokenInvalidError()

        # Step 3: load user
        user = self._users.get(user_id)
        if not user:
            raise PasswordResetTokenInvalidError()

        # Step 4: persist new password hash
        user.password_hash = hash_password(data.new_password)
        self._users.save(user)

        # Step 5: atomically mark token consumed BEFORE commit
        # (if Redis write fails we raise without committing — token stays valid
        #  for retry, which is safer than committing then failing to invalidate)
        consumed = self._denylist.consume(
            data.token,
            ttl_seconds=settings.JWT_RESET_TOKEN_EXPIRES_SECONDS,
        )
        if not consumed:
            # Race condition: another request consumed this token concurrently
            logger.warning(
                "Concurrent reset token use detected for user_id=%s.", user_id
            )
            self._uow.rollback()
            raise PasswordResetTokenInvalidError()

        self._write_audit(
            action=AuditActionType.UPDATE,
            actor_id=None,
            entity_type="user",
            entity_id=str(user.id),
            description=f"Password reset completed for '{user.email}'.",
            after={"password_hash": "[REDACTED]"},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._uow.commit()

        event_bus.publish(PasswordResetCompletedEvent(user_id=user.id))
        logger.info("Password reset completed for user %s.", user.id)

    def enroll_mfa(
        self,
        user_id: str,
        actor_id: str,
    ) -> MFASetupResponse:
        """Generate a provisional TOTP secret and return the provisioning URI.

        The secret is written as `<secret>:pending` — it is NOT active until
        `confirm_mfa_enrollment` is called with a valid TOTP code.

        Args:
            user_id: UUID string of the user starting MFA enrollment.
            actor_id: UUID string of the actor (same as user for self-service).

        Returns:
            MFASetupResponse with provisioning_uri and qr_code_data_url.

        Raises:
            NotFoundError: If no user with the given ID exists.
            BusinessRuleViolationError: If MFA is already fully enrolled.
        """
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

    def confirm_mfa_enrollment(
        self,
        user_id: str,
        totp_code: str,
        actor_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        """Verify TOTP code against the provisional secret and activate MFA.

        Args:
            user_id: UUID string of the user confirming enrollment.
            totp_code: The 6-digit code from the authenticator app.
            actor_id: UUID string of the actor (same as user for self-service).
            ip_address: Request originator IP (for audit).
            user_agent: HTTP User-Agent string (for audit).

        Raises:
            NotFoundError: If no user with the given ID exists.
            MFAInvalidError: If enrollment has not been started, or the
                TOTP code does not match the provisional secret.
        """
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

        self._write_audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=str(user.id),
            description=f"MFA enrollment confirmed for '{user.email}'.",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._uow.commit()

        event_bus.publish(MFAEnrolledEvent(user_id=user.id))
        logger.info("MFA activated for user %s.", user_id)

    def disable_mfa(
        self,
        user_id: str,
        totp_code: str,
        actor_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        """Verify TOTP code and permanently clear the MFA secret.

        Args:
            user_id: UUID string of the user disabling MFA.
            totp_code: The 6-digit code from the authenticator app.
            actor_id: UUID string of the actor (same as user for self-service).
            ip_address: Request originator IP (for audit).
            user_agent: HTTP User-Agent string (for audit).

        Raises:
            NotFoundError: If no user with the given ID exists.
            MFAInvalidError: If MFA is not currently enrolled, or the
                TOTP code is invalid.
        """
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))

        if not user.mfa_secret or user.mfa_secret.endswith(":pending"):
            raise MFAInvalidError("MFA is not currently enrolled.")

        if not verify_totp(user.mfa_secret, totp_code):
            raise MFAInvalidError()

        user.mfa_secret = None
        self._users.save(user, actor_id=actor_id)

        self._write_audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=str(user.id),
            description=f"MFA disabled for '{user.email}'.",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._uow.commit()

        event_bus.publish(MFADisabledEvent(user_id=user.id))
        logger.info("MFA disabled for user %s.", user_id)
