from __future__ import annotations
from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent


@dataclass
class UserCreatedEvent(DomainEvent):
    user_id: str = ""
    email:   str = ""
    role:    str = ""


@dataclass
class UserUpdatedEvent(DomainEvent):
    user_id: str = ""


@dataclass
class UserDeactivatedEvent(DomainEvent):
    user_id: str = ""


@dataclass
class UserReactivatedEvent(DomainEvent):
    user_id: str = ""


@dataclass
class UserPreferenceUpdatedEvent(DomainEvent):
    user_id: str = ""
