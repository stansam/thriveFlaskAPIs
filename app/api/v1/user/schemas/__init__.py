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


class UserCreateSchema(Schema):
    """First-pass validation for POST /api/v1/users/."""
    class Meta:
        unknown = RAISE

    email = fields.Email(required=True)
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    phone = fields.Str(load_default=None, validate=validate.Length(max=30), allow_none=True)
    password = fields.Str(required=True, validate=validate.Length(min=10, max=128))
    role = fields.Str(
        load_default="agent",
        validate=validate.OneOf([r.value for r in UserRole]),
    )


from app.enums import ThemePreference, DashboardLayout, PreferredChannel

class UserPreferenceUpdateSchema(Schema):
    """First-pass validation for PATCH /api/v1/users/<id>/preferences."""
    class Meta:
        unknown = RAISE

    theme = fields.Str(
        validate=validate.OneOf([e.value for e in ThemePreference]),
        allow_none=True,
    )
    timezone = fields.Str(validate=validate.Length(max=60), allow_none=True)
    language = fields.Str(validate=validate.Length(max=10), allow_none=True)
    dashboard_layout = fields.Str(
        validate=validate.OneOf([e.value for e in DashboardLayout]),
        allow_none=True,
    )
    items_per_page = fields.Int(
        validate=validate.Range(min=5, max=200),
        allow_none=True,
    )
    default_booking_channel = fields.Str(
        validate=validate.OneOf([e.value for e in PreferredChannel]),
        allow_none=True,
    )
    show_ticket_cost_column = fields.Bool(allow_none=True)
    auto_send_confirmation = fields.Bool(allow_none=True)
    notify_new_booking = fields.Bool(allow_none=True)
    notify_payment_received = fields.Bool(allow_none=True)
    notify_booking_cancelled = fields.Bool(allow_none=True)
    notify_booking_confirmed = fields.Bool(allow_none=True)
    notify_new_client = fields.Bool(allow_none=True)
    notify_referral_qualified = fields.Bool(allow_none=True)
    notify_subscription_renewal = fields.Bool(allow_none=True)
    notify_low_stock_alert = fields.Bool(allow_none=True)

