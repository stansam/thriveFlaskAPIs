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
    email = fields.String(
        required=True,
        validate=validate.Length(min=5), # TODO: Implement robust email check.
        error_messages={
            "required": "Email is required."
        }
    )
    
