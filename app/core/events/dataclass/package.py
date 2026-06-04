from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent

@dataclass
class PackageCreatedEvent(DomainEvent):
    package_id: str = ""
    title:      str = ""
    actor_id:   str | None = None

@dataclass
class PackageUpdatedEvent(DomainEvent):
    package_id: str = ""
    actor_id:   str | None = None

@dataclass
class PackagePublishedEvent(DomainEvent):
    package_id: str = ""
    title:      str = ""
    actor_id:   str | None = None

@dataclass
class PackagePausedEvent(DomainEvent):
    package_id: str = ""
    actor_id:   str | None = None

@dataclass
class PackageArchivedEvent(DomainEvent):
    package_id: str = ""
    actor_id:   str | None = None

@dataclass
class PackageDuplicatedEvent(DomainEvent):
    source_package_id: str = ""
    new_package_id:    str = ""
    new_title:         str = ""
    actor_id:          str | None = None

@dataclass
class PackageHighlightAddedEvent(DomainEvent):
    package_id:   str = ""
    highlight_id: str = ""
    actor_id:     str | None = None

@dataclass
class PackageHighlightUpdatedEvent(DomainEvent):
    package_id:   str = ""
    highlight_id: str = ""
    actor_id:     str | None = None

@dataclass
class PackageHighlightDeletedEvent(DomainEvent):
    package_id:   str = ""
    highlight_id: str = ""
    actor_id:     str | None = None

@dataclass
class PackageInclusionAddedEvent(DomainEvent):
    package_id:   str = ""
    inclusion_id: str = ""
    actor_id:     str | None = None

@dataclass
class PackageInclusionUpdatedEvent(DomainEvent):
    package_id:   str = ""
    inclusion_id: str = ""
    actor_id:     str | None = None

@dataclass
class PackageInclusionDeletedEvent(DomainEvent):
    package_id:   str = ""
    inclusion_id: str = ""
    actor_id:     str | None = None

@dataclass
class PackageItineraryDayAddedEvent(DomainEvent):
    package_id: str = ""
    day_id:     str = ""
    actor_id:   str | None = None

@dataclass
class PackageItineraryDayUpdatedEvent(DomainEvent):
    package_id: str = ""
    day_id:     str = ""
    actor_id:   str | None = None

@dataclass
class PackageItineraryDayDeletedEvent(DomainEvent):
    package_id: str = ""
    day_id:     str = ""
    actor_id:   str | None = None

@dataclass
class PackagePriceTierAddedEvent(DomainEvent):
    package_id: str = ""
    tier_id:    str = ""
    actor_id:   str | None = None

@dataclass
class PackagePriceTierUpdatedEvent(DomainEvent):
    package_id: str = ""
    tier_id:    str = ""
    actor_id:   str | None = None

@dataclass
class PackagePriceTierDeactivatedEvent(DomainEvent):
    package_id: str = ""
    tier_id:    str = ""
    actor_id:   str | None = None

@dataclass
class PackageMediaAttachedEvent(DomainEvent):
    package_id: str = ""
    asset_id:   str = ""
    media_id:   str = ""
    is_cover:   bool = False
    actor_id:   str | None = None

@dataclass
class PackageMediaRemovedEvent(DomainEvent):
    package_id: str = ""
    media_id:   str = ""
    actor_id:   str | None = None

@dataclass
class PackageInsuranceAddedEvent(DomainEvent):
    package_id:   str = ""
    insurance_id: str = ""
    actor_id:     str | None = None

@dataclass
class PackageInsuranceUpdatedEvent(DomainEvent):
    package_id:   str = ""
    insurance_id: str = ""
    actor_id:     str | None = None

@dataclass
class PackageInsuranceDeletedEvent(DomainEvent):
    package_id:   str = ""
    insurance_id: str = ""
    actor_id:     str | None = None

