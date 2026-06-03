# dtos/preference.py
from __future__ import annotations
from typing import Annotated
from pydantic import Field
from app.enums import ThemePreference, DashboardLayout, PreferredChannel, DocumentFormat
from .common import AuditFieldsMixin, StrictRequestModel

class UserPreferenceUpdateRequest(StrictRequestModel):
    theme: ThemePreference | None = None
    timezone: Annotated[str | None, Field(default=None, max_length=60)] = None
    language: Annotated[str | None, Field(default=None, max_length=10)] = None
    dashboard_layout: DashboardLayout | None = None
    items_per_page: Annotated[int | None, Field(default=None, ge=5, le=200)] = None
    default_booking_channel: PreferredChannel | None = None
    show_ticket_cost_column: bool | None = None
    auto_send_confirmation: bool | None = None
    notify_new_booking: bool | None = None
    notify_payment_received: bool | None = None
    notify_booking_cancelled: bool | None = None
    notify_booking_confirmed: bool | None = None
    notify_new_client: bool | None = None
    notify_referral_qualified: bool | None = None
    notify_subscription_renewal: bool | None = None
    notify_low_stock_alert: bool | None = None

class UserPreferenceResponse(AuditFieldsMixin):
    user_id: str
    theme: ThemePreference
    timezone: str
    language: str
    dashboard_layout: DashboardLayout
    items_per_page: int
    default_booking_channel: PreferredChannel
    show_ticket_cost_column: bool
    auto_send_confirmation: bool
    notify_new_booking: bool
    notify_payment_received: bool
    notify_booking_cancelled: bool
    notify_booking_confirmed: bool
    notify_new_client: bool
    notify_referral_qualified: bool
    notify_subscription_renewal: bool
    notify_low_stock_alert: bool

class ClientPreferenceUpdateRequest(StrictRequestModel):
    preferred_channel: PreferredChannel | None = None
    preferred_document_format: DocumentFormat | None = None
    marketing_opt_in: bool | None = None
    booking_reminders: bool | None = None
    travel_reminder_hours: Annotated[int | None, Field(default=None, ge=1, le=336)] = None
    payment_reminders: bool | None = None
    language: Annotated[str | None, Field(default=None, max_length=10)] = None
    preferred_currency_display: Annotated[str | None, Field(default=None, max_length=3)] = None
    timezone: Annotated[str | None, Field(default=None, max_length=60)] = None

class ClientPreferenceResponse(AuditFieldsMixin):
    client_id: str
    preferred_channel: PreferredChannel
    preferred_document_format: DocumentFormat
    marketing_opt_in: bool
    booking_reminders: bool
    travel_reminder_hours: int
    payment_reminders: bool
    language: str
    preferred_currency_display: str
    timezone: str
