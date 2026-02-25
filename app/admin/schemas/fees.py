from marshmallow import fields, validate
from app.schemas.base import BaseSchema

class ServiceFeeSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=50))
    amount = fields.Float(required=True, validate=validate.Range(min=0))
    currency = fields.String(load_default="USD", validate=validate.Length(equal=3))
    rule_type = fields.String(required=True, validate=validate.OneOf(['fixed', 'percentage']))
    is_active = fields.Boolean(load_default=True)
