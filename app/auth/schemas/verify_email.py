from marshmallow import fields, validate
from app.schemas.base import BaseSchema


class VerifyEmailSchema(BaseSchema):
    token = fields.String(
        required=True,
        validate=validate.Length(min=10),
        error_messages={
            "required": "Verification token is required."
        }
    )
