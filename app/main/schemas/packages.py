from marshmallow import fields, validate, pre_load
from app.schemas.base import BaseSchema

class PackageSearchSchema(BaseSchema):
    q = fields.String(required=False, allow_none=True)
    country = fields.String(required=False, allow_none=True)
    min_price = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0))
    max_price = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0))
    min_days = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    max_days = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    limit = fields.Integer(required=False, load_default=20, validate=validate.Range(min=1, max=100))
    offset = fields.Integer(required=False, load_default=0, validate=validate.Range(min=0))

    @pre_load
    def normalize_input(self, data, **kwargs):
        if "country" in data and isinstance(data["country"], str):
            data["country"] = data["country"].strip().title()
        if "q" in data and isinstance(data["q"], str):
            data["q"] = data["q"].strip()
        return data
