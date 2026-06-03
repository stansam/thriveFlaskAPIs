# app/api/v1/user/schemas/__init__.py
"""
Marshmallow request and query schemas for User API.
"""
from marshmallow import Schema, fields, validate, RAISE
from app.enums import UserRole


class UserListQuerySchema(Schema):
    role = fields.Str(
        validate=validate.OneOf([r.value for r in UserRole]),
        allow_none=True,
    )
    is_active = fields.Bool(allow_none=True)
    search = fields.Str(validate=validate.Length(max=100), allow_none=True)
    page = fields.Int(validate=validate.Range(min=1), load_default=1)
    per_page = fields.Int(
        validate=validate.Range(min=1, max=200),
        load_default=25,
    )


class UserAdminUpdateSchema(Schema):
    class Meta:
        unknown = RAISE

    full_name = fields.Str(
        validate=validate.Length(min=2, max=200),
        allow_none=True,
    )
    phone = fields.Str(validate=validate.Length(max=30), allow_none=True)
    role = fields.Str(
        validate=validate.OneOf([r.value for r in UserRole]),
        allow_none=True,
    )
    is_active = fields.Bool(allow_none=True)


class UserSelfUpdateSchema(Schema):
    class Meta:
        unknown = RAISE

    full_name = fields.Str(
        validate=validate.Length(min=2, max=200),
        allow_none=True,
    )
    phone = fields.Str(validate=validate.Length(max=30), allow_none=True)
