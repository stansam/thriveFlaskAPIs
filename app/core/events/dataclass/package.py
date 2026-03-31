from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent

@dataclass
class PackageCreatedEvent(DomainEvent):
    package_id: str = ""
    title:      str = ""
    actor_id:   str = ""

@dataclass
class PackageUpdatedEvent(DomainEvent):
    package_id: str = ""
    actor_id:   str = ""

@dataclass
class PackagePublishedEvent(DomainEvent):
    package_id: str = ""
    title:      str = ""
    actor_id:   str = ""

@dataclass
class PackagePausedEvent(DomainEvent):
    package_id: str = ""
    actor_id:   str = ""

@dataclass
class PackageArchivedEvent(DomainEvent):
    package_id: str = ""
    actor_id:   str = ""

@dataclass
class PackageDuplicatedEvent(DomainEvent):
    source_package_id: str = ""
    new_package_id:    str = ""
    new_title:         str = ""
    actor_id:          str = ""

@dataclass
class PackageHighlightAddedEvent(DomainEvent):
    package_id:   str = ""
    highlight_id: str = ""
    actor_id:     str = ""

@dataclass
class PackageHighlightUpdatedEvent(DomainEvent):
    highlight_id: str = ""
    actor_id:     str = ""

@dataclass
class PackageHighlightDeletedEvent(DomainEvent):
    highlight_id: str = ""
    actor_id:     str = ""

@dataclass
class PackageInclusionAddedEvent(DomainEvent):
    package_id:   str = ""
    inclusion_id: str = ""
    actor_id:     str = ""

@dataclass
class PackageInclusionUpdatedEvent(DomainEvent):
    inclusion_id: str = ""
    actor_id:     str = ""

@dataclass
class PackageInclusionDeletedEvent(DomainEvent):
    inclusion_id: str = ""
    actor_id:     str = ""

@dataclass
class PackageItineraryDayAddedEvent(DomainEvent):
    package_id: str = ""
    day_id:     str = ""
    actor_id:   str = ""

@dataclass
class PackageItineraryDayUpdatedEvent(DomainEvent):
    day_id:   str = ""
    actor_id: str = ""

@dataclass
class PackageItineraryDayDeletedEvent(DomainEvent):
    day_id:   str = ""
    actor_id: str = ""

@dataclass
class PackagePriceTierAddedEvent(DomainEvent):
    package_id: str = ""
    tier_id:    str = ""
    actor_id:   str = ""

@dataclass
class PackagePriceTierUpdatedEvent(DomainEvent):
    tier_id:  str = ""
    actor_id: str = ""

@dataclass
class PackagePriceTierDeactivatedEvent(DomainEvent):
    tier_id:  str = ""
    actor_id: str = ""
