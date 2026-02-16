from app.models import NotificationTemplate
from sqlalchemy.orm import Session
from jinja2 import Template
from app.repository.email.exceptions import TemplateNotFound, TemplateRenderingError, EmailSendingFailed
from app.repository.email.ops.send import SendEmail

class SendEmailTemplate:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.sender = SendEmail()

    def execute(self, to_email: str, trigger_event: str, context: dict) -> bool:
        # Fetch template
        template = self.db.query(NotificationTemplate).filter_by(trigger_event=trigger_event, is_active=True).first()
        
        if not template:
            # Fallback or error? For specific trigger events, we expect templates.
            raise TemplateNotFound(f"No active email template found for event: {trigger_event}")

        try:
            # Render Subject
            subject_tmpl = Template(template.subject_template)
            subject = subject_tmpl.render(**context)
            
            # Render Body
            body_tmpl = Template(template.body_html_template)
            body_html = body_tmpl.render(**context)
            
            # Send
            return self.sender.execute(to_email, subject, body_html)
            
        except Exception as e:
            if isinstance(e, EmailSendingFailed):
                raise
            raise TemplateRenderingError(f"Failed to render email template: {str(e)}") from e
