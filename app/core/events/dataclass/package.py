from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent

@dataclass
class PackagePublishedEvent(DomainEvent):
    package_id: str = ""
    title:      str = ""
    actor_id:   str = ""
