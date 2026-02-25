from marshmallow import fields
from app.schemas.base import BaseSchema

class CompanyStatusSchema(BaseSchema):
    is_active = fields.Boolean(required=True)
