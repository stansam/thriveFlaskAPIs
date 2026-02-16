from app.schemas import BaseSchema
from app.models.enums import Gender
from marshmallow import fields, validate, ValidationError, pre_load, validates_schema

class RegisterSchema(BaseSchema):
    first_name = fields.Str(required=True, validate=validate.Length(min=3, max=20))
    last_name = fields.Str(required=True, validate=validate.Length(min=3, max=20))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    confirm_password = fields.Str(required=True, load_only=True)
    gender = fields.Str(required=True, validate=validate.OneOf(g.value for g in Gender))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(min=7, max=20))
    
    @pre_load
    def normalize_input(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()

        if "email" in data:
            data["email"] = data["email"].lower()

        return data

    @validates_schema
    def validate_passwords(self, value):
        if value["password"] != value["confirm_password"]:
            raise ValidationError({
                "confirm_password":"Passwords do not match"})
