import pytest
from unittest.mock import patch, MagicMock
from app.repository.email.services import EmailService
from flask import Flask

@pytest.fixture
def email_service(db_session):
    return EmailService(db_session)

@patch('app.repository.email.ops.send.send_async_email.delay')
def test_send_email_async(mock_delay, email_service):
    """Test that send_email triggers the celery task."""
    to = "test@example.com"
    subject = "Test"
    body = "<p>Body</p>"
    
    # Mock the return value of delay
    mock_task = MagicMock()
    mock_task.id = "123"
    mock_delay.return_value = mock_task

    result = email_service.send_email(to, subject, body)
    
    assert result is True
    mock_delay.assert_called_once_with(to, subject, body, None)

@patch('app.repository.email.ops.render.render_template')
def test_render_template(mock_render, email_service, app):
    """Test that render_template calls flask's render_template correctly."""
    mock_render.return_value = "<html>Rendered</html>"
    
    with app.app_context():
        result = email_service.render_template("welcome.html", {"name": "Test"})
        
    assert result == "<html>Rendered</html>"
    # Verify path adjustment logic if applicable
    # The current implementation checks startswith "email/"
    mock_render.assert_called_once()
    args, kwargs = mock_render.call_args
    assert args[0] == "email/welcome.html"
    assert kwargs == {"name": "Test"}

@patch('app.repository.email.ops.render.render_template')
def test_send_template_legacy_wrapper(mock_render, email_service, app):
    """Test that the legacy send_template method works as an alias."""
    mock_render.return_value = "<html>Body</html>"
    
    with app.app_context():
        result = email_service.send_template("reset.html", {})
        
    assert result == "<html>Body</html>"
    mock_render.assert_called_once()
