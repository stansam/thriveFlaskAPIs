from marshmallow import fields, validate
from app.schemas.base import BaseSchema

class ManagePackageSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=3, max=100))
    slug = fields.String(required=True, validate=validate.Length(min=3, max=100))
    description = fields.String(required=True, validate=validate.Length(min=10, max=2000))
    price = fields.Float(required=True, validate=validate.Range(min=0.01))
    currency = fields.String(load_default="USD", validate=validate.Length(equal=3))
    duration_days = fields.Integer(required=True, validate=validate.Range(min=1))
    country = fields.String(required=True)
    is_featured = fields.Boolean(load_default=False)
    is_active = fields.Boolean(load_default=True)
    available_slots = fields.Integer(load_default=0, validate=validate.Range(min=0))
