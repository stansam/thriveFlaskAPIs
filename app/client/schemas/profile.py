from marshmallow import fields, validate, pre_load
from app.schemas import BaseSchema
from app.models.enums import Gender

class UpdateProfileSchema(BaseSchema):
    first_name = fields.Str(required=False, validate=validate.Length(min=2, max=50))
    last_name = fields.Str(required=False, validate=validate.Length(min=2, max=50))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(min=7, max=20))
    gender = fields.Str(required=False, allow_none=True, validate=validate.OneOf(Gender.list()))
    avatar_url = fields.URL(required=False, allow_none=True)
    locale = fields.Str(required=False, allow_none=True)

    @pre_load
    def normalize_input(self, data, **kwargs):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()
        return data

class UpdatePreferencesSchema(BaseSchema):
    email_notifications = fields.Boolean(required=False)
    sms_notifications = fields.Boolean(required=False)
    marketing_opt_in = fields.Boolean(required=False)
    currency = fields.Str(required=False, validate=validate.Length(equal=3))
    timezone = fields.Str(required=False)
