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

from pydantic import EmailStr, Field, field_validator, model_validator

from app.enums import UserRole
from .common import AuditFieldsMixin, StrictRequestModel, ResponseModel

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

class UserUpdateRequest(StrictRequestModel):
    """PATCH /admin/users/{id} — partial update."""

    full_name: Annotated[str | None, Field(default=None, min_length=2, max_length=200)]
    phone: Annotated[str | None, Field(default=None, max_length=30)]
    role: UserRole | None = None
    is_active: bool | None = None

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
    totp_code: Annotated[str | None, Field(default=None, max_length=6)] = None

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
            "mfa_enrolled": user.mfa_secret is not None,
            "last_login_at": user.last_login_at,
        })

class TokenResponse(ResponseModel):
    """POST /auth/login response."""
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
