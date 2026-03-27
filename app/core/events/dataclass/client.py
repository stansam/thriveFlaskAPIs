from dataclasses import dataclass, field
from app.core.events.dataclass.base import DomainEvent

@dataclass
class ClientCreatedEvent(DomainEvent):
    client_id:   str = ""
    email:       str = ""
    referred_by: str | None = None


@dataclass
class ClientUpdatedEvent(DomainEvent):
    client_id: str = ""
    fields_changed: list[str] = field(default_factory=list)
