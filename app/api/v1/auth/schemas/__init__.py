# app/api/v1/auth/schemas/__init__.py
"""
Marshmallow request validation schemas for Auth API.
"""
from marshmallow import Schema, fields, validate, RAISE


class LoginSchema(Schema):
    class Meta:
        unknown = RAISE

    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1))
    totp_code = fields.Str(load_default=None, validate=validate.Regexp(r'^\d{6}$'))


class PasswordChangeSchema(Schema):
    class Meta:
        unknown = RAISE

    current_password = fields.Str(required=True, validate=validate.Length(min=1))
    new_password = fields.Str(required=True, validate=validate.Length(min=10, max=128))
    confirm_password = fields.Str(required=True, validate=validate.Length(min=10, max=128))


class ForgotPasswordSchema(Schema):
    class Meta:
        unknown = RAISE

    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    class Meta:
        unknown = RAISE

    token = fields.Str(required=True, validate=validate.Length(min=1))
    new_password = fields.Str(required=True, validate=validate.Length(min=10, max=128))
    confirm_password = fields.Str(required=True, validate=validate.Length(min=10, max=128))


class MFAConfirmSchema(Schema):
    class Meta:
        unknown = RAISE

    totp_code = fields.Str(required=True, validate=validate.Regexp(r'^\d{6}$'))


class MFADisableSchema(Schema):
    class Meta:
        unknown = RAISE

    totp_code = fields.Str(required=True, validate=validate.Regexp(r'^\d{6}$'))
