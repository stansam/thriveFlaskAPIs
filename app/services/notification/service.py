import logging
from flask import current_app
from dataclasses import asdict
from app.repository import repositories
from app.dto.notification.schemas import DispatchNotificationDTO, SendEmailDTO
from app.services.notification.utils import compile_jinja_template
from app.tasks.email_tasks import dispatch_async_email

class NotificationService:
    """
    NotificationService orchestrates fetching active communication templates,
    injecting dynamic runtime context payloads, and deploying them securely
    over standard SMTP explicitly configured natively to handle App Passwords.
    """

    def __init__(self):
        self.notification_repo = repositories.notification
        self.user_repo = repositories.user

    def dispatch_notification(self, payload: DispatchNotificationDTO) -> bool:
        """
        Translates a trigger event (e.g. 'BOOKING_CONFIRMED') into a fully
        compiled email explicitly delegating routing towards `send_email`.
        """
        user = self.user_repo.get_by_id(payload.user_id)
        if not user or not user.email:
            # Drop silently if user uncontactable natively avoiding spam logs
            return False

        # Find the active universal template
        from app.models.notification import NotificationTemplate
        template = NotificationTemplate.query.filter_by(
            trigger_event=payload.trigger_event, 
            is_active=True
        ).first()

        if not template:
            # We don't raise errors here natively since notifications are often silent async downstream hooks
            return False

        # Apply variables (e.g. {{ first_name }})
        subject = compile_jinja_template(template.subject_template or "", payload.context)
        body = compile_jinja_template(template.body_html_template or "", payload.context)

        # Dispatch physical email mapping
        email_payload = SendEmailDTO(
            to_email=user.email,
            subject=subject,
            body_html=body
        )
        return self.send_email(email_payload)

    def send_email(self, payload: SendEmailDTO) -> bool:
        """
        Abstracts the email firing dropping the payload natively into the Background Worker
        binding directly around the `@celery.task` dropping synchronous waits perfectly.
        """
        # Dictionary format strictly passing to Redis safely
        payload_dict = asdict(payload)
        
        try:
            # Drop the physical block offload onto background fabric identically
            dispatch_async_email.delay(payload_dict)
            return True
        except Exception as e:
            current_app.logger.error(f"Failed delegating SMTP payload physically across Celery boundaries: {str(e)}")
            return False
