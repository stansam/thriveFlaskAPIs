from celery import shared_task
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import logging

logger = logging.getLogger(__name__)

@shared_task(ignore_result=False, bind=True, max_retries=3, default_retry_delay=60)
def send_async_email(self, to_email: str, subject: str, body_html: str, from_email: str = None):
    """
    Background task to send an email via SMTP.
    """
    try:
        smtp_server = current_app.config.get('MAIL_SERVER')
        smtp_port = current_app.config.get('MAIL_PORT')
        smtp_user = current_app.config.get('MAIL_USERNAME')
        smtp_password = current_app.config.get('MAIL_PASSWORD')
        use_tls = current_app.config.get('MAIL_USE_TLS')
        default_sender = current_app.config.get('MAIL_DEFAULT_SENDER')

        if not from_email:
            from_email = default_sender

        if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
             logger.warning("Email configuration missing. Email will not be sent.")
             return "Configuration missing"

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_html, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            
        logger.info(f"Email sent successfully to {to_email}")
        return f"Sent to {to_email}"

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        self.retry(exc=e)
