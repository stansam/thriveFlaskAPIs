"""
Authentication Service.

Provides domain operations for authentication, session management,
passwords, and MFA lifecycle. Uses flask-login for establishing sessions.
Orchestrates domain models, handles business logic, and logs audit events.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from flask_login import login_user, logout_user
from app.dto import(
    LoginRequest, PasswordChangeRequest, ForgotPasswordResponse,
    PasswordResetRequest
)
from app.core.errors.handlers import (
    MFARequiredError,
    MFAInvalidError,
    AccountInactiveError,
    InvalidCredentialsError,
    NotFoundError,
    BusinessRuleViolationError,
    ValidationError_
)
from app.core.events import event_bus
from app.core.events.dataclass import(
    UserLoggedInEvent, UserLoggedOutEvent, PasswordChangedEvent,
    PasswordResetRequestedEvent, PasswordResetCompletedEvent,
    MFADisabledEvent, MFAEnrolledEvent
)
from app.core.security import (
    hash_password,
    verify_password,
    password_needs_rehash,
    generate_totp_secret,
    get_totp_provisioning_uri,
    verify_totp,
    create_reset_token,
    verify_reset_token,
    generate_totp_qr_data_url
)
from app.core.auth_user import FlaskLoginUser
from app.dto.user import UserResponse, MFASetupResponse
from app.enums import AuditActionType
from app.repository.user import UserRepository
from app.repository.audit import AuditLogRepository

logger = logging.getLogger(__name__)

class AuthService:
    """Service handling authentication flows and security management."""

    def __init__(
        self,
        user_repo: UserRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._users = user_repo
        self._audits = audit_repo
        # TODO: implement itsdangerous or similar. 
        self._reset_tokens: dict[str, str] = {} # token -> email

    def _commit(self) -> None:
        """Utility method to orchestrate commit block for write operations."""
        self._users._session.commit()

    def _rollback(self) -> None:
        """Utility method to orchestrate rollback."""
        self._users._session.rollback()
    
    def _write_audit(
        self,
        action: AuditActionType,
        actor_id: str | None,
        entity_type: str,
        entity_id: str | None = None,
        description: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Write an immutable audit log entry within the current session."""
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

    def login(
        self,
        data: LoginRequest,
        ip_address: str = "" ,
        user_agent: str = ""
    ) -> UserResponse:
        """
        Authenticate user, evaluate active status, manage MFA challenge,
        stamp last login, establish session, and audit.

        Raises:
            InvalidCredentialsError
            InactiveAccountError
        """
        user = self._users.find_by_email(data.email)

        dummy_hash = "$argon2id$v=19$m=65536,t=3,p=4$fakefakefakefake$fakefakefakefake"
        check_hash = user.password_hash if user else dummy_hash

        if not verify_password(data.password, check_hash) or user is None:
            logger.warning(
                "Failed login attempt for email '%s' from %s",
                email,
                ip_address,
            )
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountInactiveError()

        if user.mfa_secret:
            if not data.totp_code:
                raise MFARequiredError()
            if not verify_totp(user.mfa_secret, data.totp_code):
                raise MFAInvalidError()
        
        if password_needs_rehash(user.password_hash):
            user.password_hash = hash_password(data.password)
            logger.info("Re-hashed password for user %s (parameter upgrade).", user.id)

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
        self._commit()
        
        # Session establishment
        flask_user = FlaskLoginUser(user)
        login_user(flask_user, remember=False)

        event_bus.publish(UserLoggedInEvent(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        ))

        logger.info("Successful login: user=%s role=%s ip=%s", user.id, user.role.value, ip_address)
        return UserResponse.from_user(user)

    def logout(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> None:
        """Log out current user and write audit event."""
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(user_id=user_id)

        self._write_audit(
            action=AuditActionType.LOGOUT,
            actor_id=user.id,
            entity_type="user",
            entity_id=user.id,
            description=f"User '{user.email}' logged out.",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._commit()
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
        """Verify current password, enforce strength policy, hash, save, audit."""
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(user_id=user_id)

        if not verify_password(data.current_password, user.password_hash):
            raise InvalidCredentialsError("Current password incorrect.")

        if data.current_password == data.new_password:
            raise BusinessRuleViolationError("New password must be different.")
        before = {"password_hash": "[REDACTED]"}
        user.password_hash = hash_password(data.new_password)
        self._users.save(user, actor_id=actor_id)
        
        self._write_audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            description=f"Password changed for user '{user.email}'.",
            before=before,
            after={"password_hash": "[REDACTED]"},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._commit()

        event_bus.publish(PasswordChangedEvent(user_id=user.id))
        logger.info("Password changed for user %s.", user.id)

    def request_password_reset(
        self,
        email: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> ForgotPasswordResponse:
        """
        Generate time-limited signed reset token, dispatch 'PASSWORD_RESET'
        notification. Always return success to prevent email enumeration.
        """
        user = self._users.find_by_email(email)
        if user and user.is_active:
            reset_token = create_reset_token(user.id)
            self._write_audit(
                action=AuditActionType.UPDATE,
                actor_id=None,
                entity_type="user",
                entity_id=user.id,
                description=f"Password reset requested for '{user.email}'.",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self._commit()

            event_bus.publish(PasswordResetRequestedEvent(
                user_id=user.id,
                reset_token=reset_token,
                email=user.email,
            ))
            logger.info("Password reset requested for user %s.", user.id)
            return ForgotPasswordResponse(success=True)
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
        user_agent: str = ""
    ) -> None:
        """Validate token, hash & persist new, invalidate token, write AuditLog."""
        user_id = verify_reset_token(data.token)
        user = self._users.get(user_id)
        email = self._reset_tokens.get(data.token)

        if not email:
            raise ValidationError_("Invalid or expired reset token.")

        if user.email != email:
            raise ValidationError_("Invalid or expired reset token.")
        
        user.password_hash = hash_password(data.new_password)
        self._users.save(user)
        
        del self._reset_tokens[data.token]

        self._write_audit(
            action=AuditActionType.UPDATE,
            actor_id=None,
            entity_type="user",
            entity_id=user.id,
            description=f"Password reset completed for '{user.email}'.",
            after={"password_hash": "[REDACTED]"},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._commit()

        event_bus.publish(PasswordResetCompletedEvent(user_id=user.id))
        logger.info("Password reset completed for user %s.", user.id)

    def enroll_mfa(
        self,
        user_id: str,
        actor_id: str,
    ) -> MFASetupResponse:
        """
        Generate TOTP secret, return provisioning URI.
        Secret is NOT persisted until confirm_mfa_enrollment.
        """
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(user_id=user_id)

        if user.mfa_secret:
            raise BusinessRuleViolationError("MFA is already enrolled.")

        provisional_secret = generate_totp_secret()
        user.mfa_secret = f"{provisional_secret}:pending"
        self._users.save(user, actor_id=actor_id)

        provisioning_uri = get_totp_provisioning_uri(provisional_secret, user.email)
        qr_data_url = generate_totp_qr_data_url(provisioning_uri)

        self._commit()

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
        """Verify TOTP code against provisional secret, persist mfa_secret on User."""
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(user_id=user_id)

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
            entity_id=user.id,
            description=f"MFA enrollment confirmed for '{user.email}'.",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._commit()

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
        """Verify TOTP, set mfa_secret = NULL."""
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(user_id=user_id)

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
            entity_id=user.id,
            description=f"MFA disabled for '{user.email}'.",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._commit()

        event_bus.publish(MFADisabledEvent(user_id=user.id))
        logger.info("MFA disabled for user %s.", user_id)
