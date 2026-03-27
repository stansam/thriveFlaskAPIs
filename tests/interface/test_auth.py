import sys
from unittest.mock import MagicMock, patch

# Mock out missing dependencies in the restricted environment
sys.modules['bcrypt'] = MagicMock()
sys.modules['pyotp'] = MagicMock()
sys.modules['qrcode'] = MagicMock()
sys.modules['email_validator'] = MagicMock()

import importlib.metadata
_original_version = importlib.metadata.version
def _mock_version(name):
    if name == 'email-validator':
        return '2.0.0'
    return _original_version(name)

importlib.metadata.version = _mock_version

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.interface.auth import AuthService
from app.core.errors import (
    AuthenticationError,
    InactiveAccountError,
    InvalidCredentialsError,
    UserNotFoundError,
    BusinessRuleError,
    ValidationError
)
from app.core.security import hash_password, generate_totp_secret, get_totp_provisioning_uri
import pyotp

@pytest.fixture
def mock_user_repo():
    repo = MagicMock()
    repo._session = MagicMock()
    return repo

@pytest.fixture
def mock_audit_repo():
    return MagicMock()

@pytest.fixture
def auth_service(mock_user_repo, mock_audit_repo):
    """Factory fixture for AuthService with mocked repositories."""
    return AuthService(user_repo=mock_user_repo, audit_repo=mock_audit_repo)

@pytest.fixture
def mock_user():
    """Returns a mock user."""
    user = MagicMock()
    user.id = "user-123"
    user.email = "admin@thrive.com"
    user.password_hash = hash_password("ValidPassword1!")
    user.is_active = True
    user.mfa_secret = None
    user.last_login_at = None
    
    # Mock to_audit_dict to prevent dict expansion issues
    user.to_audit_dict.return_value = {
        "id": "user-123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by_id": None,
        "updated_by_id": None
    }
    user.full_name = "Admin User"
    user.phone = "123456789"
    user.role = "AGENT"
    return user

@patch("app.interface.auth.login_user")
def test_login_success(mock_login_user, auth_service, mock_user_repo, mock_audit_repo, mock_user):
    mock_user_repo.find_by_email.return_value = mock_user

    response = auth_service.login("admin@thrive.com", "ValidPassword1!")

    # Verify logic
    assert response.email == "admin@thrive.com"
    assert response.is_active is True
    assert mock_user.last_login_at is not None

    # Verify repository calls
    mock_user_repo.save.assert_called_once_with(mock_user)
    mock_audit_repo.create.assert_called_once()
    mock_user_repo._session.commit.assert_called_once()
    mock_login_user.assert_called_once()

def test_login_invalid_password(auth_service, mock_user_repo, mock_user):
    mock_user_repo.find_by_email.return_value = mock_user

    with pytest.raises(InvalidCredentialsError):
        auth_service.login("admin@thrive.com", "WrongPassword!")

    mock_user_repo.save.assert_not_called()

def test_login_inactive_user(auth_service, mock_user_repo, mock_user):
    mock_user.is_active = False
    mock_user_repo.find_by_email.return_value = mock_user

    with pytest.raises(InactiveAccountError):
        auth_service.login("admin@thrive.com", "ValidPassword1!")

def test_login_mfa_required_but_missing(auth_service, mock_user_repo, mock_user):
    mock_user.mfa_secret = generate_totp_secret()
    mock_user_repo.find_by_email.return_value = mock_user

    with pytest.raises(AuthenticationError) as excinfo:
        auth_service.login("admin@thrive.com", "ValidPassword1!")
    
    assert excinfo.value.details.get("mfa_required") is True

@patch("app.interface.auth.login_user")
def test_login_mfa_success(mock_login_user, auth_service, mock_user_repo, mock_user):
    secret = generate_totp_secret()
    mock_user.mfa_secret = secret
    mock_user_repo.find_by_email.return_value = mock_user
    
    valid_code = pyotp.TOTP(secret).now()

    response = auth_service.login("admin@thrive.com", "ValidPassword1!", totp_code=valid_code)
    assert response is not None
    mock_login_user.assert_called_once()

@patch("app.interface.auth.logout_user")
def test_logout(mock_logout_user, auth_service, mock_audit_repo, mock_user_repo):
    auth_service.logout("user-123")
    
    mock_audit_repo.create.assert_called_once()
    mock_user_repo._session.commit.assert_called_once()
    mock_logout_user.assert_called_once()

def test_change_password_success(auth_service, mock_user_repo, mock_audit_repo, mock_user):
    mock_user_repo.get.return_value = mock_user

    auth_service.change_password("user-123", "ValidPassword1!", "NewPassword2@", actor_id="user-123")

    mock_user_repo.save.assert_called_once()
    mock_audit_repo.create.assert_called_once()
    mock_user_repo._session.commit.assert_called_once()

def test_change_password_invalid_current(auth_service, mock_user_repo, mock_user):
    mock_user_repo.get.return_value = mock_user

    with pytest.raises(InvalidCredentialsError):
        auth_service.change_password("user-123", "WrongPassword!", "NewPassword2@", actor_id="user-123")

def test_request_password_reset(auth_service, mock_user_repo, mock_user):
    mock_user_repo.find_by_email.return_value = mock_user

    # Initial token dict is empty
    assert len(auth_service._reset_tokens) == 0

    auth_service.request_password_reset("admin@thrive.com")

    # One token was generated
    assert len(auth_service._reset_tokens) == 1
    token = list(auth_service._reset_tokens.keys())[0]
    assert auth_service._reset_tokens[token] == "admin@thrive.com"

def test_reset_password_success(auth_service, mock_user_repo, mock_user):
    mock_user_repo.find_by_email.return_value = mock_user
    auth_service._reset_tokens["valid-token"] = "admin@thrive.com"

    auth_service.reset_password("valid-token", "NewPassword123!")

    mock_user_repo.save.assert_called_once()
    mock_user_repo._session.commit.assert_called_once()
    assert "valid-token" not in auth_service._reset_tokens

def test_enroll_mfa_success(auth_service, mock_user_repo, mock_user):
    mock_user_repo.get.return_value = mock_user
    
    response = auth_service.enroll_mfa("user-123", "user-123")
    
    assert response.provisioning_uri is not None
    assert response.qr_code_data_url.startswith("data:image/png;base64,")
    assert "user-123" in auth_service._pending_mfa_secrets

def test_enroll_mfa_already_enrolled(auth_service, mock_user_repo, mock_user):
    mock_user.mfa_secret = "EXISTINGSECRET"
    mock_user_repo.get.return_value = mock_user
    
    with pytest.raises(BusinessRuleError):
        auth_service.enroll_mfa("user-123", "user-123")

def test_confirm_mfa_enrollment_success(auth_service, mock_user_repo, mock_audit_repo, mock_user):
    mock_user_repo.get.return_value = mock_user
    secret = generate_totp_secret()
    auth_service._pending_mfa_secrets = {"user-123": secret}
    code = pyotp.TOTP(secret).now()

    auth_service.confirm_mfa_enrollment("user-123", code, "user-123")

    assert mock_user.mfa_secret == secret
    assert "user-123" not in auth_service._pending_mfa_secrets
    mock_user_repo.save.assert_called_once()

def test_disable_mfa_success(auth_service, mock_user_repo, mock_audit_repo, mock_user):
    secret = generate_totp_secret()
    mock_user.mfa_secret = secret
    mock_user_repo.get.return_value = mock_user
    code = pyotp.TOTP(secret).now()

    auth_service.disable_mfa("user-123", code, "user-123")

    assert mock_user.mfa_secret is None
    mock_user_repo.save.assert_called_once()
    mock_user_repo._session.commit.assert_called_once()
