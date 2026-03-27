from __future__ import annotations
from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent


@dataclass
class UserLoggedInEvent(DomainEvent):
    user_id:    str = ""
    ip_address: str = ""
    user_agent: str = ""


@dataclass
class UserLoggedOutEvent(DomainEvent):
    user_id: str = ""


@dataclass
class PasswordChangedEvent(DomainEvent):
    user_id: str = ""


@dataclass
class PasswordResetRequestedEvent(DomainEvent):
    user_id:     str = ""
    reset_token: str = ""
    email:       str = ""


@dataclass
class PasswordResetCompletedEvent(DomainEvent):
    user_id: str = ""


@dataclass
class MFAEnrolledEvent(DomainEvent):
    user_id: str = ""


@dataclass
class MFADisabledEvent(DomainEvent):
    user_id: str = ""