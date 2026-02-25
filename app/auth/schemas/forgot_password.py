from marshmallow import fields, pre_load
from app.schemas import BaseSchema

class ForgotPasswordSchema(BaseSchema):
    email = fields.Email(required=True)

    @pre_load
    def normalize_input(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()

        if "email" in data:
            data["email"] = data["email"].lower()

        return data
