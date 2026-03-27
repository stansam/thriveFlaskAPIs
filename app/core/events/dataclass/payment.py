from dataclasses import dataclass
from app.core.events.dataclass.base import DomainEvent


@dataclass
class PaymentReceivedEvent(DomainEvent):
    payment_id:  str = ""
    booking_id:  str = ""
    client_id:   str = ""
    amount_usd:  str = "0.00"
    method:      str = ""
    actor_id:    str = ""


@dataclass
class PaymentRefundedEvent(DomainEvent):
    payment_id:    str = ""
    booking_id:    str = ""
    client_id:     str = ""
    refund_amount: str = "0.00"
    reason:        str = ""
    actor_id:      str = ""
