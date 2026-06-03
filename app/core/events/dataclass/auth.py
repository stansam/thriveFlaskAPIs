from __future__ import annotations
from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent


@dataclass
class UserLoggedInEvent(DomainEvent):
    user_id:    str = ""
    ip_address: str = ""
    user_agent: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")


@dataclass
class UserLoggedOutEvent(DomainEvent):
    user_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")


@dataclass
class PasswordChangedEvent(DomainEvent):
    user_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")


@dataclass
class PasswordResetRequestedEvent(DomainEvent):
    """
    Event published when a password reset is requested.
    Contains the raw reset token (secret-in-transit).
    """
    user_id:     str = ""
    reset_token: str = ""
    email:       str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.email:
            raise ValueError("email is required")


@dataclass
class PasswordResetCompletedEvent(DomainEvent):
    user_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")


@dataclass
class MFAEnrolledEvent(DomainEvent):
    user_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")


@dataclass
class MFADisabledEvent(DomainEvent):
    user_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")