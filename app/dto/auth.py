# app/dto/auth.py
from __future__ import annotations
from typing import Annotated
from pydantic import EmailStr, Field, field_validator, model_validator
from app.dto.common import StrictRequestModel
from app.enums import UserRole
import re

class UserRegistrationRequest(StrictRequestModel):
    """POST /api/v1/auth/register — Agent self-registration."""
    full_name: Annotated[str, Field(min_length=2, max_length=200)]
    email: EmailStr
    password: Annotated[str, Field(min_length=10, max_length=128)]
    confirm_password: Annotated[str, Field(min_length=10, max_length=128)]
    phone: Annotated[str | None, Field(default=None, max_length=30)] = None

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
        if not re.match(r"^\+[1-9]\d{6,14}$", clean_v):
            raise ValueError(
                "Phone number must be in international format (e.g., +1234567890) "
                "with a '+' followed by 7 to 15 digits."
            )
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegistrationRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self
