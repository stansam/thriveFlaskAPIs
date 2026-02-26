from celery import shared_task
from flask import current_app
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@shared_task(ignore_result=True)
def dispatch_async_email(payload_dict: dict) -> bool:
    """
    Executes an explicit physical SMTP connection bounded out-of-band by Celery.
    Safely captures Flask context parameters scaling seamlessly via Redis constraints.
    """
    smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('MAIL_PORT', 587)
    smtp_user = current_app.config.get('MAIL_USERNAME')
    smtp_password = current_app.config.get('MAIL_PASSWORD')
    use_tls = current_app.config.get('MAIL_USE_TLS', True)

    if not smtp_user or not smtp_password:
        current_app.logger.warning("Async Notification bypass: SMTP credentials missing natively.")
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = payload_dict.get('subject')
    msg['From'] = f"Thrive Global Travel <{smtp_user}>"
    msg['To'] = payload_dict.get('to_email')

    # Attach explicit HTML content body payload natively
    msg.attach(MIMEText(payload_dict.get('body_html'), 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        if use_tls:
            server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, payload_dict.get('to_email'), msg.as_string())
        server.quit()
        return True
    except Exception as e:
        current_app.logger.error(f"Failed Async SMTP proxy physical connection securely: {str(e)}")
        return False
