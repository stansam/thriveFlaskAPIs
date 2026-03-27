from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent

@dataclass
class ReferralQualifiedEvent(DomainEvent):
    referral_id:  str = ""
    referrer_id:  str = ""
    referee_id:   str = ""
    credit_usd:   str = "10.00"
