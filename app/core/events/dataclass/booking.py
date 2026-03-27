from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent


@dataclass
class BookingCreatedEvent(DomainEvent):
    booking_id:       str = ""
    reference_number: str = ""
    client_id:        str = ""
    service_type:     str = ""
    actor_id:         str = ""


@dataclass
class BookingStatusChangedEvent(DomainEvent):
    booking_id:       str = ""
    reference_number: str = ""
    client_id:        str = ""
    old_status:       str = ""
    new_status:       str = ""
    actor_id:         str = ""
    reason:           str | None = None


@dataclass
class BookingConfirmedEvent(DomainEvent):
    booking_id:       str = ""
    reference_number: str = ""
    client_id:        str = ""
    actor_id:         str = ""


@dataclass
class BookingCancelledEvent(DomainEvent):
    booking_id:       str = ""
    reference_number: str = ""
    client_id:        str = ""
    reason:           str = ""
    actor_id:         str = ""


@dataclass
class BookingCompletedEvent(DomainEvent):
    booking_id:       str = ""
    reference_number: str = ""
    client_id:        str = ""

