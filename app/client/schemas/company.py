from marshmallow import fields, validate, pre_load
from app.schemas import BaseSchema

class EmployeeInviteSchema(BaseSchema):
    first_name = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(min=7, max=20))

    @pre_load
    def normalize_input(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()
        if "email" in data:
            data["email"] = data["email"].lower()
        return data
