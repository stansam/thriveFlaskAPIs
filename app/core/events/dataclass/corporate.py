from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent

@dataclass
class SubscriptionRenewedEvent(DomainEvent):
    account_id:      str = ""
    subscription_id: str = ""
    tier:            str = ""


@dataclass
class SubscriptionLimitWarningEvent(DomainEvent):
    account_id:      str = ""
    subscription_id: str = ""
    bookings_used:   int = 0
    bookings_limit:  int = 0
