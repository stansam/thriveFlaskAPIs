from marshmallow import fields, validate
from app.schemas.base import BaseSchema


class GoogleOAuthSchema(BaseSchema):
    id_token = fields.String(
        required=True,
        validate=validate.Length(min=10)
    )

    remember_me = fields.Boolean(
        required=False,
        load_default=False
    )

class GoogleOAuthData(BaseSchema):
    sub = fields.String(required=True)
    email = fields.String(required=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    avatar_url = fields.String(required=True)
    locale = fields.String(required=True)
    email_verified = fields.Boolean(required=True)
    iss = fields.String(required=True, validate=validate.OneOf(["accounts.google.com", "https://accounts.google.com"]))

    