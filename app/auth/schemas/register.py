from marshmallow import fields, validate, ValidationError, pre_load, validates_schema
from app.schemas import BaseSchema
from app.models.enums import Gender

class RegisterSchema(BaseSchema):
    first_name = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    email = fields.Email(required=True)
    password = fields.Str(
        required=True, 
        load_only=True, 
        validate=[
            validate.Length(min=8, max=128),
            validate.Regexp(
                regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]+$',
                error="Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character natively."
            )
        ]
    )
    confirm_password = fields.Str(required=True, load_only=True)
    
    gender = fields.Str(required=False, allow_none=True, validate=validate.OneOf(Gender.list()))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(min=7, max=20))
    locale = fields.Str(required=False, allow_none=True)
    company_id = fields.Str(required=False, allow_none=True, validate=validate.Length(equal=36))

    @pre_load
    def normalize_input(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()

        if "email" in data:
            data["email"] = data["email"].lower()

        return data

    @validates_schema
    def validate_passwords(self, value, **kwargs):
        if value.get("password") != value.get("confirm_password"):
            raise ValidationError({"confirm_password": "Passwords do not match."})
