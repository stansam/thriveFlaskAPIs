# services/notification_service.py
"""
NotificationService — multi-channel notification dispatch.

Implements interfaces.md § 12. NotificationService.

Delivery pipeline per notification:
  1. Look up active templates for the event_type (all channels + language)
  2. Render subject + body via Jinja2
  3. Create Notification row (in-app inbox entry)
  4. Create NotificationDelivery rows per opted-in channel
  5. Attempt delivery synchronously (console / sendgrid / wati)
  6. Update delivery status
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from jinja2 import Environment, TemplateSyntaxError, BaseLoader
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import select, and_
from app.models.base import db
from app.enums import (
    AuditActionType,
    NotificationEventType, NotificationChannel,
    NotificationPriority, NotificationStatus, DeliveryStatus,
    RecipientType, BookingStatus
)
from app.models.booking import Booking
from app.models.notification import Notification
from app.models.notification_template import NotificationTemplate
from app.models.notification_delivery import NotificationDelivery
from app.core.logging import get_logger
from app.core.config import settings
from app.core.errors.handlers import BadRequestError, NotFoundError, BusinessRuleViolationError
from app.dto import (
    NotificationDeliveryResponse,
    NotificationListResponse,
    NotificationResponse,
    NotificationTemplateCreateRequest,
    NotificationTemplateResponse,
    NotificationTemplateUpdateRequest,
)
from app.repository import (
    notification_repo,
    notification_template_repo,
    notification_delivery_repo,
    user_repo,
    user_preference_repo,
    client_repo,
    client_preference_repo,
    booking_repo,
    corporate_subscription_repo
)
from app.interface._base import BaseService

logger = get_logger(__name__)

_JINJA_ENV = SandboxedEnvironment(loader=BaseLoader())
_MAX_RETRIES = 3


class NotificationService(BaseService):
    # Core dispatch
    def dispatch(
        self,
        event_type: NotificationEventType,
        recipient_type: RecipientType,
        recipient_id: str,
        context: dict[str, Any],
        entity_type: str | None = None,
        entity_id: str | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_for: datetime | None = None,
    ) -> Notification:
        """
        Create and send a notification to a single recipient.

        Steps
        -----
        1. Determine recipient's preferred language.
        2. Fetch all active templates for the event_type.
        3. Render the IN_APP template (always) → title + body.
        4. Create Notification row.
        5. For each channel the recipient has enabled:
           create NotificationDelivery + attempt send.
        6. Flush but do NOT commit here — caller commits.
        """
        language = _get_language(recipient_type, recipient_id)
        templates = notification_template_repo.find_all_for_event(event_type)

        in_app_tpl = _pick(templates, NotificationChannel.IN_APP, language)
        if in_app_tpl:
            subject, body = self.render_template(in_app_tpl.id, context)
        else:
            subject = event_type.value.replace("_", " ").title()
            body = str(context)

        import json
        notif = Notification(
            template_id=in_app_tpl.id if in_app_tpl else None,
            event_type=event_type,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            title=subject or event_type.value,
            body=body,
            context_json=json.dumps(context, default=str),
            entity_type=entity_type,
            entity_id=entity_id,
            status=NotificationStatus.PENDING,
            priority=priority,
            scheduled_for=scheduled_for,
        )
        notif.set_creator(recipient_id)
        db.session.add(notif)
        db.session.flush()

        # Build delivery rows for enabled channels
        channels = _get_enabled_channels(recipient_type, recipient_id, event_type)
        for channel in channels:
            if channel == NotificationChannel.IN_APP:
                continue   # handled by Notification row itself
            tpl = _pick(templates, channel, language)
            if not tpl:
                continue
            sub, rendered = self.render_template(tpl.id, context)
            address = _get_address(recipient_type, recipient_id, channel)
            delivery = NotificationDelivery(
                notification_id=notif.id,
                channel=channel,
                status=DeliveryStatus.QUEUED,
                recipient_address=address,
                attempt_number=1,
            )
            delivery.set_creator(recipient_id)
            db.session.add(delivery)
            db.session.flush()
            self._attempt_delivery(delivery, sub, rendered)

        notif.status = NotificationStatus.SENDING
        db.session.flush()
        return notif

    def dispatch_to_all_staff(
        self,
        event_type: NotificationEventType,
        context: dict[str, Any],
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> list[Notification]:
        """Dispatch to all active users subscribed to this event."""
        all_users = user_repo.find_all_active()
        notifications: list[Notification] = []
        for user in all_users:
            pref = user_preference_repo.get_or_create(user_id=user.id)
            if _user_subscribed(pref, event_type):
                notif = self.dispatch(
                    event_type=event_type,
                    recipient_type=RecipientType.USER,
                    recipient_id=user.id,
                    context=context,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
                notifications.append(notif)
        db.session.commit()
        return notifications
    # Template rendering
    def render_template(
        self, template_id: str, context: dict[str, Any]
    ) -> tuple[str, str]:
        tpl = notification_template_repo.get_or_404(template_id)
        try:
            subject = (
                _JINJA_ENV.from_string(tpl.subject).render(**context)
                if tpl.subject else ""
            )
            body = _JINJA_ENV.from_string(tpl.body).render(**context)
        except Exception as exc:
            logger.warning("Template render error (id=%s): %s", template_id, exc)
            subject = tpl.subject or ""
            body = tpl.body
        return subject, body
    # Inbox
    def get_inbox(
        self,
        recipient_type: RecipientType,
        recipient_id: str,
        unread_only: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> NotificationListResponse:
        result = notification_repo.find_for_recipient(
            recipient_type, recipient_id, unread_only=unread_only,
            page=page, per_page=per_page,
        )
        unread = notification_repo.unread_count(recipient_type, recipient_id)
        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in result.items],
            total=result.total,
            unread_count=unread,
            page=result.page,
            per_page=result.per_page,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    def get_unread_count(
        self, recipient_type: RecipientType, recipient_id: str
    ) -> int:
        return notification_repo.unread_count(recipient_type, recipient_id)

    def mark_read(
        self, notification_id: str, recipient_id: str
    ) -> NotificationResponse:
        notif = notification_repo.get_or_404(notification_id)
        if notif.recipient_id != recipient_id:
            from app.core.errors.handlers import PermissionDeniedError
            raise PermissionDeniedError("You do not own this notification.")
        notification_repo.mark_read(notif)
        db.session.commit()
        return NotificationResponse.model_validate(notif)

    def mark_all_read(
        self, recipient_type: RecipientType, recipient_id: str
    ) -> int:
        count = notification_repo.mark_all_read(recipient_type, recipient_id)
        db.session.commit()
        return count

    def dismiss(
        self, notification_id: str, recipient_id: str
    ) -> NotificationResponse:
        notif = notification_repo.get_or_404(notification_id)
        if notif.recipient_id != recipient_id:
            from app.core.errors.handlers import PermissionDeniedError
            raise PermissionDeniedError("You do not own this notification.")
        notification_repo.update(
            notif,
            status=NotificationStatus.DISMISSED,
            dismissed_at=datetime.now(timezone.utc),
        )
        db.session.commit()
        return NotificationResponse.model_validate(notif)
    # Delivery retry + webhooks
    def retry_failed_delivery(
        self, delivery_id: str, actor_id: str
    ) -> NotificationDeliveryResponse:
        delivery = notification_delivery_repo.get_or_404(delivery_id)
        if delivery.status != DeliveryStatus.FAILED:
            raise BadRequestError("Only FAILED deliveries can be retried.")
        if delivery.attempt_number >= _MAX_RETRIES:
            raise BusinessRuleViolationError(
                f"Maximum retry attempts ({_MAX_RETRIES}) reached for delivery {delivery_id}."
            )
        notification_delivery_repo.update(
            delivery,
            status=DeliveryStatus.RETRYING,
            attempt_number=delivery.attempt_number + 1,
            next_retry_at=None,
            failed_at=None,
            failure_reason=None,
        )
        notif = notification_repo.get(delivery.notification_id)
        if notif:
            _, body = self.render_template(notif.template_id, {}) if notif.template_id else ("", notif.body)
            self._attempt_delivery(delivery, notif.title, body)
        db.session.commit()
        return NotificationDeliveryResponse.model_validate(delivery)

    def process_provider_webhook(self, provider: str, payload: dict) -> None:
        """Handle delivery receipt / bounce / open webhooks."""
        if provider == "sendgrid":
            self._handle_sendgrid_webhook(payload)
        elif provider == "wati":
            self._handle_wati_webhook(payload)
        else:
            logger.warning("Unknown webhook provider: %s", provider)
        db.session.commit()

    def _handle_sendgrid_webhook(self, payload: dict) -> None:
        events = payload if isinstance(payload, list) else [payload]
        for event in events:
            msg_id = event.get("sg_message_id", "").split(".")[0]
            delivery = notification_delivery_repo.find_by_provider_message_id(msg_id)
            if not delivery:
                continue
            event_type = event.get("event", "")
            now = datetime.now(timezone.utc)
            if event_type == "delivered":
                notification_delivery_repo.update(delivery, status=DeliveryStatus.DELIVERED, delivered_at=now)
            elif event_type == "open":
                notification_delivery_repo.update(delivery, status=DeliveryStatus.OPENED, opened_at=now)
            elif event_type in ("bounce", "dropped", "deferred"):
                notification_delivery_repo.update(
                    delivery, status=DeliveryStatus.BOUNCED if event_type == "bounce" else DeliveryStatus.FAILED,
                    failed_at=now, failure_reason=event.get("reason", event_type),
                )

    def _handle_wati_webhook(self, payload: dict) -> None:
        msg_id = payload.get("whatsappMessageId", "")
        delivery = notification_delivery_repo.find_by_provider_message_id(msg_id)
        if not delivery:
            return
        status = payload.get("status", "")
        now = datetime.now(timezone.utc)
        if status == "sent":
            notification_delivery_repo.update(delivery, status=DeliveryStatus.SENT, sent_at=now)
        elif status == "delivered":
            notification_delivery_repo.update(delivery, status=DeliveryStatus.DELIVERED, delivered_at=now)
        elif status == "read":
            notification_delivery_repo.update(delivery, status=DeliveryStatus.OPENED, opened_at=now)
        elif status in ("failed", "undelivered"):
            notification_delivery_repo.update(
                delivery, status=DeliveryStatus.FAILED, failed_at=now,
                failure_reason=payload.get("errorMessage", status),
            )
    # Template management
    def create_template(
        self, data: NotificationTemplateCreateRequest, actor_id: str
    ) -> NotificationTemplateResponse:
        try:
            _JINJA_ENV.from_string(data.body)
        except TemplateSyntaxError as exc:
            raise BadRequestError(f"Invalid Jinja2 template syntax: {exc}")

        tpl = notification_template_repo.create(
            actor_id=actor_id,
            event_type=data.event_type,
            channel=data.channel,
            language=data.language,
            name=data.name,
            subject=data.subject,
            body=data.body,
            variable_schema=data.variable_schema,
            version=1,
            is_active=data.is_active,
        )
        self._audit(AuditActionType.CREATE, actor_id, "notification_template", tpl.id,
                    description=f"Template '{data.name}' created.")
        db.session.commit()
        return NotificationTemplateResponse.model_validate(tpl)

    def update_template(
        self, template_id: str, data: NotificationTemplateUpdateRequest, actor_id: str
    ) -> NotificationTemplateResponse:
        tpl = notification_template_repo.get_or_404(template_id)
        if data.body:
            try:
                _JINJA_ENV.from_string(data.body)
            except TemplateSyntaxError as exc:
                raise BadRequestError(f"Invalid Jinja2 template syntax: {exc}")
        updates = data.model_dump(exclude_none=True)
        updates["version"] = tpl.version + 1
        notification_template_repo.update(tpl, actor_id=actor_id, **updates)
        self._audit(AuditActionType.UPDATE, actor_id, "notification_template", template_id,
                    description=f"Template '{tpl.name}' updated to v{updates['version']}.")
        db.session.commit()
        return NotificationTemplateResponse.model_validate(tpl)

    def list_templates(
        self, event_type=None, channel=None, is_active=None,
        page: int = 1, per_page: int = 25
    ) -> dict:
        stmt = select(NotificationTemplate)
        if event_type:
            stmt = stmt.where(NotificationTemplate.event_type == event_type)
        if channel:
            stmt = stmt.where(NotificationTemplate.channel == channel)
        if is_active is not None:
            stmt = stmt.where(NotificationTemplate.is_active.is_(is_active))
        stmt = stmt.order_by(NotificationTemplate.event_type, NotificationTemplate.channel)
        result = notification_template_repo.paginate(stmt, page=page, per_page=per_page)
        items = [NotificationTemplateResponse.model_validate(t) for t in result.items]
        return {"items": items, **self._page_meta(result)}
    # Background job entry points
    def schedule_pre_trip_reminders(self, hours_before: int = 48) -> int:
        """Find confirmed bookings departing within `hours_before` hours and remind."""
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) + timedelta(hours=hours_before)).date()
        bookings = booking_repo.find_confirmed_upcoming(cutoff)
        dispatched = 0
        for b in bookings:
            depart = getattr(b, "departure_date", None) or getattr(b, "travel_date", None)
            context = {
                "reference_number": b.reference_number,
                "hours_until_departure": hours_before,
                "departure_datetime": str(depart),
                "client_first_name": "",
            }
            client = client_repo.get(b.client_id)
            if client:
                context["client_first_name"] = client.first_name
            self.dispatch(
                event_type=NotificationEventType.BOOKING_REMINDER_PRE_TRIP,
                recipient_type=RecipientType.CLIENT,
                recipient_id=b.client_id,
                context=context,
                entity_type="booking",
                entity_id=b.id,
            )
            dispatched += 1
        if dispatched:
            db.session.commit()
        return dispatched

    def schedule_balance_reminders(self) -> int:
        """Remind clients with outstanding balances older than 48h."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
        stmt = select(Booking).where(
            Booking.status == BookingStatus.PENDING_PAYMENT,
            Booking.created_at <= cutoff,
        )
        bookings = list(db.session.execute(stmt).scalars().all())
        dispatched = 0
        for b in bookings:
            self.dispatch(
                event_type=NotificationEventType.BOOKING_REMINDER_BALANCE,
                recipient_type=RecipientType.CLIENT,
                recipient_id=b.client_id,
                context={"reference_number": b.reference_number},
                entity_type="booking",
                entity_id=b.id,
            )
            dispatched += 1
        if dispatched:
            db.session.commit()
        return dispatched

    def schedule_subscription_warnings(self, days_before_expiry: int = 7) -> int:
        """Warn corporate accounts whose subscription expires within N days."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) + timedelta(days=days_before_expiry)
        subs = corporate_subscription_repo.find_expiring_before(cutoff)
        dispatched = 0
        for sub in subs:
            self.dispatch_to_all_staff(
                event_type=NotificationEventType.SUBSCRIPTION_EXPIRING,
                context={
                    "account_id": sub.account_id,
                    "tier": sub.tier.value,
                    "expires_on": str(sub.billing_cycle_end.date()),
                    "days_remaining": days_before_expiry,
                },
                entity_type="corporate_subscription",
                entity_id=sub.id,
            )
            dispatched += 1
        return dispatched
    # Delivery execution
    def _attempt_delivery(
        self, delivery: NotificationDelivery, subject: str, body: str
    ) -> None:
        now = datetime.now(timezone.utc)
        try:
            if delivery.channel == NotificationChannel.EMAIL:
                self._send_email(delivery, subject, body)
            elif delivery.channel == NotificationChannel.WHATSAPP:
                self._send_whatsapp(delivery, body)
            elif delivery.channel == NotificationChannel.SMS:
                self._send_sms(delivery, body)
            delivery.status = DeliveryStatus.SENT
            delivery.sent_at = now
        except Exception as exc:
            logger.error(
                "Delivery failed [%s] notif=%s: %s",
                delivery.channel.value, delivery.notification_id, exc,
            )
            delivery.status = DeliveryStatus.FAILED
            delivery.failed_at = now
            delivery.failure_reason = str(exc)[:499]
        db.session.flush()

    def _send_email(
        self, delivery: NotificationDelivery, subject: str, body: str
    ) -> None:
        backend = settings.EMAIL_BACKEND
        if backend == "console":
            logger.info(
                "[EMAIL CONSOLE] To: %s | Subject: %s\n%s",
                delivery.recipient_address, subject, body,
            )
            return
        if backend == "sendgrid":
            import sendgrid
            from sendgrid.helpers.mail import Mail
            sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            mail = Mail(
                from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
                to_emails=delivery.recipient_address,
                subject=subject,
                plain_text_content=body,
            )
            resp = sg.send(mail)
            delivery.provider_name = "sendgrid"
            delivery.provider_message_id = resp.headers.get("X-Message-Id", "")
            return
        raise NotImplementedError(f"Email backend '{backend}' not implemented.")

    def _send_whatsapp(
        self, delivery: NotificationDelivery, body: str
    ) -> None:
        if not settings.WATI_API_URL or not settings.WATI_API_KEY:
            logger.info(
                "[WHATSAPP CONSOLE] To: %s\n%s",
                delivery.recipient_address, body,
            )
            return
        import httpx
        url = f"{settings.WATI_API_URL}/api/v1/sendSessionMessage/{delivery.recipient_address}"
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {settings.WATI_API_KEY}"},
            json={"messageText": body},
            timeout=10,
        )
        resp.raise_for_status()
        delivery.provider_name = "wati"
        delivery.provider_message_id = resp.json().get("id", "")

    def _send_sms(
        self, delivery: NotificationDelivery, body: str
    ) -> None:
        logger.info("[SMS CONSOLE] To: %s\n%s", delivery.recipient_address, body)
# Helper
def _get_language(recipient_type: RecipientType, recipient_id: str) -> str:
    try:
        if recipient_type == RecipientType.CLIENT:
            pref = client_preference_repo.find_by_client(recipient_id)
            return pref.language if pref else "en"
        pref = user_preference_repo.find_by_user(recipient_id)
        return pref.language if pref else "en"
    except Exception:
        return "en"


def _get_address(
    recipient_type: RecipientType, recipient_id: str, channel: NotificationChannel
) -> str | None:
    try:
        if recipient_type == RecipientType.CLIENT:
            client = client_repo.get(recipient_id)
            if channel == NotificationChannel.EMAIL:
                return client.email if client else None
            if channel == NotificationChannel.WHATSAPP:
                return (client.whatsapp_number or client.phone) if client else None
        user = user_repo.get(recipient_id)
        if channel == NotificationChannel.EMAIL:
            return user.email if user else None
    except Exception:
        return None
    return None


def _get_enabled_channels(
    recipient_type: RecipientType,
    recipient_id: str,
    event_type: NotificationEventType,
) -> list[NotificationChannel]:
    channels = [NotificationChannel.IN_APP]
    try:
        if recipient_type == RecipientType.CLIENT:
            pref = client_preference_repo.find_by_client(recipient_id)
            if pref:
                channels.append(NotificationChannel(pref.preferred_channel.value))
        else:
            channels.append(NotificationChannel.EMAIL)
    except Exception:
        channels.append(NotificationChannel.EMAIL)
    return list(dict.fromkeys(channels))   # deduplicate preserving order


def _pick(templates, channel: NotificationChannel, language: str):
    for t in templates:
        if t.channel == channel and t.language == language:
            return t
    for t in templates:
        if t.channel == channel and t.language == "en":
            return t
    return None


def _user_subscribed(pref, event_type: NotificationEventType) -> bool:
    mapping = {
        NotificationEventType.BOOKING_CREATED:    "notify_new_booking",
        NotificationEventType.PAYMENT_RECEIVED:   "notify_payment_received",
        NotificationEventType.BOOKING_CANCELLED:  "notify_booking_cancelled",
        NotificationEventType.BOOKING_CONFIRMED:  "notify_booking_confirmed",
        NotificationEventType.CLIENT_WELCOME:     "notify_new_client",
        NotificationEventType.SUBSCRIPTION_RENEWED: "notify_subscription_renewal",
        NotificationEventType.SUBSCRIPTION_EXPIRING: "notify_subscription_renewal",
    }
    attr = mapping.get(event_type)
    if attr:
        return bool(getattr(pref, attr, True))
    return True   # default: receive all other event types


notification_service = NotificationService()