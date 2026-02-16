from marshmallow import fields, validate, validates_schema, ValidationError
from app.schemas.base import BaseSchema


class ResetPasswordSchema(BaseSchema):
    token = fields.String(required=True, validate=validate.Length(min=10),
     error_messages={"required": "Reset token is required."})
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))
    confirm_password = fields.String(required=True, load_only=True)

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        if data.get("password") != data.get("confirm_password"):
            raise ValidationError(
                {"confirm_password": ["Passwords do not match."]}
            )
