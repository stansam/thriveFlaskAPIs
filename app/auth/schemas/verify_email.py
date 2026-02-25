from marshmallow import fields
from app.schemas import BaseSchema

class VerifyEmailSchema(BaseSchema):
    token = fields.Str(required=True)
