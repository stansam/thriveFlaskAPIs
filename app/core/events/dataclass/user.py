from dataclasses import dataclass, field
from app.core.events.dataclass.base import DomainEvent


@dataclass
class UserCreatedEvent(DomainEvent):
    user_id: str = ""
    email: str = ""
    role: str = ""
    full_name: str = ""
    actor_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.email:
            raise ValueError("email is required")
        if not self.role:
            raise ValueError("role is required")
        if not self.full_name:
            raise ValueError("full_name is required")
        if not self.actor_id:
            raise ValueError("actor_id is required")


@dataclass
class UserUpdatedEvent(DomainEvent):
    user_id: str = ""
    changed_fields: list[str] = field(default_factory=list)
    actor_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.actor_id:
            raise ValueError("actor_id is required")


@dataclass
class UserDeactivatedEvent(DomainEvent):
    user_id: str = ""
    actor_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.actor_id:
            raise ValueError("actor_id is required")


@dataclass
class UserReactivatedEvent(DomainEvent):
    user_id: str = ""
    actor_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.actor_id:
            raise ValueError("actor_id is required")


@dataclass
class UserPreferenceUpdatedEvent(DomainEvent):
    user_id: str = ""
    changed_fields: list[str] = field(default_factory=list)
    actor_id: str = ""

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.actor_id:
            raise ValueError("actor_id is required")


