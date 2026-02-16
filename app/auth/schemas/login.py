from marshmallow import fields, validate
from app.schemas.base import BaseSchema
from app.models.enums import UserRole


class LoginSchema(BaseSchema):
    email = fields.Email(required=True)
    password = fields.String(required=True)
    rememberMe = fields.Boolean(required=False)


class RegisterSchema(BaseSchema):
    email = fields.Email(required=True)
    password = fields.String(required=True)
    firstName = fields.String(required=True)
    lastName = fields.String(required=True)
    phone = fields.String(required=True)
    role = fields.String(required=True, validate=validate.OneOf([UserRole.CLIENT.value, UserRole.ADMIN.value]))
    