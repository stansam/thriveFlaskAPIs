from app.repository.email.services import EmailService
from app.repository.email.exceptions import (
    EmailServiceException,
    EmailSendingFailed,
    TemplateNotFound,
    TemplateRenderingError
)
