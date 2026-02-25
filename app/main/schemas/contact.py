from marshmallow import fields, validate, pre_load
from app.schemas.base import BaseSchema

class ContactFormSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    subject = fields.String(required=True, validate=validate.Length(min=5, max=150))
    message = fields.String(required=True, validate=validate.Length(min=10, max=2000))

    @pre_load
    def normalize_input(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()
        if "email" in data:
            data["email"] = data["email"].lower()
        return data
