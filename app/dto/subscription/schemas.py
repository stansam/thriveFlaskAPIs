from dataclasses import dataclass
from app.models.enums import PaymentMethod, EntityType

@dataclass
class SubscribeToPlanDTO:
    entity_id: str
    entity_type: EntityType
    plan_id: str
    payment_method: PaymentMethod

@dataclass
class UpgradePlanDTO:
    subscription_id: str
    new_plan_id: str
