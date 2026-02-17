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