from marshmallow import fields, validate
from app.schemas import BaseSchema

class SubscriptionUpgradeSchema(BaseSchema):
    new_plan_id = fields.Str(required=True, validate=validate.Length(equal=36))
