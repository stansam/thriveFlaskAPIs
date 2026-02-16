import pytest
from app.repository.email.services import EmailService
from app.models import NotificationTemplate
from app.repository.email.exceptions import TemplateNotFound

def test_send_email_direct(db_session):
    service = EmailService(db_session)
    result = service.send_email("test@example.com", "Subject", "Body")
    assert result is True

def test_send_template_success(db_session):
    service = EmailService(db_session)
    
    # Create template
    tmpl = NotificationTemplate(
        trigger_event="welcome_email",
        name="Welcome Email",
        subject_template="Welcome {{ name }}!",
        body_html_template="<h1>Hello {{ name }}</h1>"
    )
    db_session.add(tmpl)
    db_session.commit()
    
    result = service.send_template(
        "user@example.com", 
        "welcome_email", 
        {"name": "Alice"}
    )
    assert result is True

def test_send_template_not_found(db_session):
    service = EmailService(db_session)
    with pytest.raises(TemplateNotFound):
        service.send_template("user@example.com", "unknown_event", {})
