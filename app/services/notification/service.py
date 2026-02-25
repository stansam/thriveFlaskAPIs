import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from app.repository import repositories
from app.dto.notification.schemas import DispatchNotificationDTO, SendEmailDTO
from app.services.notification.utils import compile_jinja_template

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
        Abstracts purely the synchronous SMTP configuration binding directly
        into the explicit Gmail host securely bypassing local mocking contexts.
        """
        smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('MAIL_PORT', 587)
        smtp_user = current_app.config.get('MAIL_USERNAME')
        smtp_password = current_app.config.get('MAIL_PASSWORD')
        use_tls = current_app.config.get('MAIL_USE_TLS', True)

        if not smtp_user or not smtp_password:
             current_app.logger.warning("Notification bypass: SMTP credentials missing natively.")
             return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = payload.subject
        msg['From'] = f"Thrive Global Travel <{smtp_user}>"
        msg['To'] = payload.to_email

        # Attach explicit HTML content body payload natively
        msg.attach(MIMEText(payload.body_html, 'html'))

        try:
             server = smtplib.SMTP(smtp_server, smtp_port)
             if use_tls:
                  server.starttls()
             server.login(smtp_user, smtp_password)
             server.sendmail(smtp_user, payload.to_email, msg.as_string())
             server.quit()
             return True
        except Exception as e:
             current_app.logger.error(f"Failed SMTP proxy connection mapped bounds safely: {str(e)}")
             return False
