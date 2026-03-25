# dtos/notification.py
from __future__ import annotations
from datetime import datetime
from typing import Annotated
from pydantic import Field
from app.enums import (
    NotificationEventType, NotificationChannel, NotificationPriority,
    NotificationStatus, DeliveryStatus, RecipientType,
)
from .common import AuditFieldsMixin, StrictRequestModel, ResponseModel

class NotificationTemplateCreateRequest(StrictRequestModel):
    event_type: NotificationEventType
    channel: NotificationChannel
    language: Annotated[str, Field(default="en", max_length=10)] = "en"
    name: Annotated[str, Field(min_length=2, max_length=200)]
    subject: Annotated[str | None, Field(default=None, max_length=500)] = None
    body: Annotated[str, Field(min_length=1)]
    variable_schema: str | None = None
    is_active: bool = True

class NotificationTemplateUpdateRequest(StrictRequestModel):
    name: str | None = None
    subject: str | None = None
    body: str | None = None
    variable_schema: str | None = None
    is_active: bool | None = None

class NotificationTemplateResponse(AuditFieldsMixin):
    event_type: NotificationEventType
    channel: NotificationChannel
    language: str
    name: str
    subject: str | None
    body: str
    variable_schema: str | None
    version: int
    is_active: bool

class NotificationDeliveryResponse(AuditFieldsMixin):
    notification_id: str
    channel: NotificationChannel
    status: DeliveryStatus
    recipient_address: str | None
    provider_name: str | None
    provider_message_id: str | None
    attempt_number: int
    sent_at: datetime | None
    delivered_at: datetime | None
    opened_at: datetime | None
    failed_at: datetime | None
    failure_reason: str | None
    next_retry_at: datetime | None

class NotificationResponse(AuditFieldsMixin):
    template_id: str | None
    event_type: NotificationEventType
    recipient_type: RecipientType
    recipient_id: str
    title: str
    body: str
    entity_type: str | None
    entity_id: str | None
    status: NotificationStatus
    priority: NotificationPriority
    read_at: datetime | None
    dismissed_at: datetime | None
    scheduled_for: datetime | None
    deliveries: list[NotificationDeliveryResponse] = []

class NotificationListResponse(ResponseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
