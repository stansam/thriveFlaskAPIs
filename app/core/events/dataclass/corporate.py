from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent

@dataclass
class CorporateAccountCreatedEvent(DomainEvent):
    account_id:   str = ""
    company_name: str = ""

@dataclass
class CorporateAccountUpdatedEvent(DomainEvent):
    account_id: str = ""

@dataclass
class CorporateAccountDeactivatedEvent(DomainEvent):
    account_id: str = ""

@dataclass
class SubscriptionCreatedEvent(DomainEvent):
    account_id:      str = ""
    subscription_id: str = ""
    tier:            str = ""

@dataclass
class SubscriptionUpgradedEvent(DomainEvent):
    account_id:      str = ""
    subscription_id: str = ""
    new_tier:        str = ""

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
