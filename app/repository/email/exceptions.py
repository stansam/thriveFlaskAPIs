class EmailServiceException(Exception):
    """Base exception for Email Service"""
    pass

class EmailSendingFailed(EmailServiceException):
    """Raised when email sending fails"""
    pass

class TemplateNotFound(EmailServiceException):
    """Raised when an email template cannot be found"""
    pass

class TemplateRenderingError(EmailServiceException):
    """Raised when template rendering fails"""
    pass
