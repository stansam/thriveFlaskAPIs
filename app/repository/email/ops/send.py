import logging
from app.repository.email.exceptions import EmailSendingFailed

logger = logging.getLogger(__name__)

class SendEmail:
    def execute(self, to_email: str, subject: str, body_html: str, from_email: str = None) -> bool:
        try:
            # In a real implementation, this would use SMTP or an API like SendGrid/AWS SES
            # For now, we mock it by logging
            logger.info(f"--- MOCK EMAIL SENDING ---")
            logger.info(f"To: {to_email}")
            logger.info(f"From: {from_email or 'system@thrivetravels.com'}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {body_html[:100]}...") # Log first 100 chars
            logger.info(f"--------------------------")
            
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise EmailSendingFailed(f"Failed to send email: {str(e)}") from e
