from marshmallow import fields, validate, pre_load
from app.schemas import BaseSchema

class LoginSchema(BaseSchema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8))
    remember_me = fields.Boolean(required=False, missing=False)

    @pre_load
    def normalize_input(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()

        if "email" in data:
            data["email"] = data["email"].lower()

        return data


