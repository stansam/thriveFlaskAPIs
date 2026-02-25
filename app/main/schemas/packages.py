from marshmallow import fields, validate, pre_load
from app.schemas.base import BaseSchema

class PackageSearchSchema(BaseSchema):
    country = fields.String(required=False, allow_none=True)
    duration_days_min = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    duration_days_max = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    limit = fields.Integer(required=False, load_default=20, validate=validate.Range(min=1, max=100))
    offset = fields.Integer(required=False, load_default=0, validate=validate.Range(min=0))

    @pre_load
    def normalize_input(self, data, **kwargs):
        if "country" in data and isinstance(data["country"], str):
            data["country"] = data["country"].strip().title()
        return data
