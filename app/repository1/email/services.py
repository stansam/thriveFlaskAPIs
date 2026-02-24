from sqlalchemy.orm import Session
from app.repository.email.ops import (
    SendEmail,
    SendEmailTemplate,
    RenderTemplate
)

class EmailService:
    def __init__(self, db: Session):
        self.db = db
        self._sender = SendEmail()
        self._renderer = RenderTemplate()

    def send_email(self, to_email: str, subject: str, body_html: str, from_email: str = None) -> bool:
        return self._sender.execute(to_email, subject, body_html, from_email)

    def render_template(self, template_name: str, context: dict) -> str:
        """Renders an email template and returns the HTML string."""
        return self._renderer.execute(template_name, context)

    def send_template(self, template_name: str, context: dict) -> str:
        """
        Legacy/Convenience method: Renders the template and returns the body.
        The name is confusing (it currently returns body in usage, see email.py), 
        so we align it with `render_template`.
        """
        return self.render_template(template_name, context)
