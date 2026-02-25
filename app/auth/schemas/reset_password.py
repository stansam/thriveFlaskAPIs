from marshmallow import fields, validate, ValidationError, validates_schema
from app.schemas import BaseSchema

class ResetPasswordSchema(BaseSchema):
    token = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    confirm_password = fields.Str(required=True, load_only=True)

    @validates_schema
    def validate_passwords(self, value, **kwargs):
        if value.get("password") != value.get("confirm_password"):
            raise ValidationError({"confirm_password": "Passwords do not match."})
