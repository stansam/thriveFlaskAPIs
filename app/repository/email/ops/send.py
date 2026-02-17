from app.repository.email.tasks import send_async_email
import logging

logger = logging.getLogger(__name__)

class SendEmail:
    def execute(self, to_email: str, subject: str, body_html: str, from_email: str = None) -> bool:
        try:
            task = send_async_email.delay(to_email, subject, body_html, from_email)
            logger.info(f"Email task queued: {task.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to queue email task: {str(e)}")
            # TODO: Check if True return is necessary
            return False
