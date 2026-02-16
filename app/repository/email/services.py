from sqlalchemy.orm import Session
from app.repository.email.ops import (
    SendEmail,
    SendEmailTemplate
)

class EmailService:
    def __init__(self, db: Session):
        self.db = db
        self._sender = SendEmail()

    def send_email(self, to_email: str, subject: str, body_html: str, from_email: str = None) -> bool:
        return self._sender.execute(to_email, subject, body_html, from_email)

    def send_template(self, to_email: str, trigger_event: str, context: dict) -> bool:
        return SendEmailTemplate(self.db).execute(to_email, trigger_event, context)
