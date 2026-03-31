from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent

@dataclass
class FeeScheduleCreatedEvent(DomainEvent):
    schedule_id: str = ""
    name:        str = ""

@dataclass
class FeeScheduleActivatedEvent(DomainEvent):
    schedule_id: str = ""

@dataclass
class FeeScheduleDeactivatedEvent(DomainEvent):
    schedule_id: str = ""

@dataclass
class ServiceFeeAddedEvent(DomainEvent):
    schedule_id: str = ""
    fee_id:      str = ""

@dataclass
class ServiceFeeUpdatedEvent(DomainEvent):
    fee_id: str = ""

@dataclass
class ServiceFeeDeactivatedEvent(DomainEvent):
    fee_id: str = ""

@dataclass
class FeeSnapshotCreatedEvent(DomainEvent):
    booking_id: str = ""
    fee_id:     str = ""
