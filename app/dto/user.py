# dtos/user.py
"""
User DTOs.

Covers:
  - CRUD shapes for platform operators (admin/agent)
  - Auth shapes: login request, token response, password change
  - MFA enrollment response
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from dataclasses import dataclass

from pydantic import EmailStr, Field, field_validator, model_validator

from app.enums import UserRole
from app.dto.common import AuditFieldsMixin, StrictRequestModel, ResponseModel

# Requests
class UserCreateRequest(StrictRequestModel):
    """POST /admin/users — create a new platform operator."""

    full_name: Annotated[str, Field(min_length=2, max_length=200)]
    email: EmailStr
    phone: Annotated[str | None, Field(default=None, max_length=30)]
    password: Annotated[str, Field(min_length=10, max_length=128)]
    role: UserRole = UserRole.AGENT

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        clean_v = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        import re
        if not re.match(r"^\+[1-9]\d{6,14}$", clean_v):
            raise ValueError(
                "Phone number must be in international format (e.g., +1234567890) "
                "with a '+' followed by 7 to 15 digits."
            )
        return v

class UserUpdateRequest(StrictRequestModel):
    """PATCH /admin/users/{id} — partial update."""

    full_name: Annotated[str | None, Field(default=None, min_length=2, max_length=200)]
    phone: Annotated[str | None, Field(default=None, max_length=30)]
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        clean_v = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        import re
        if not re.match(r"^\+[1-9]\d{6,14}$", clean_v):
            raise ValueError(
                "Phone number must be in international format (e.g., +1234567890) "
                "with a '+' followed by 7 to 15 digits."
            )
        return v

class PasswordChangeRequest(StrictRequestModel):
    """POST /auth/change-password"""

    current_password: Annotated[str, Field(min_length=1)]
    new_password: Annotated[str, Field(min_length=10, max_length=128)]
    confirm_password: Annotated[str, Field(min_length=10, max_length=128)]

    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordChangeRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("new_password and confirm_password do not match.")
        return self

class PasswordResetRequest(StrictRequestModel):
    """POST /auth/reset-password (token-based)"""
    token: str
    new_password: Annotated[str, Field(min_length=10, max_length=128)]
    confirm_password: Annotated[str, Field(min_length=10, max_length=128)]

    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordResetRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self

class LoginRequest(StrictRequestModel):
    """POST /auth/login"""
    email: EmailStr
    password: str
    totp_code: Annotated[
        str | None,
        Field(
            default=None,
            min_length=6,
            max_length=6,
            pattern=r"^\d{6}$",
            description="6-digit TOTP code. Required when MFA is enrolled.",
        ),
    ] = None

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()

# Responses
class UserResponse(AuditFieldsMixin):
    """Full user profile returned to admin endpoints."""
    full_name: str
    email: str
    phone: str | None
    role: UserRole
    is_active: bool
    mfa_enrolled: bool = Field(default=False)
    last_login_at: datetime | None

    @classmethod
    def from_user(cls, user) -> "UserResponse":
        return cls.model_validate({
            **user.to_audit_dict(),
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_active": user.is_active,
            "mfa_enrolled": user.mfa_is_enrolled,
            "last_login_at": user.last_login_at,
        })

class TokenResponse(ResponseModel):
    """
    POST /auth/login response shape — RESERVED FOR FUTURE JWT MIGRATION.
    Currently unused: the system uses Flask-Login session cookies (not JWT).
    Do not remove without updating this comment.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until token expiry.")
    user: UserResponse

class MFASetupResponse(ResponseModel):
    """GET /auth/mfa/setup — returned to initiate TOTP enrollment."""
    provisioning_uri: str
    qr_code_data_url: str = Field(description="Base-64 data URL of the QR code PNG.")

class ForgotPasswordResponse(ResponseModel):
    message: str = "If that email is registered, a reset link has been sent."

@dataclass(frozen=True)
class UserListResult:
    items: list[UserResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
