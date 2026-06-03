"""
Integration tests for Auth API endpoints.
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock
from http import HTTPStatus
import pytest

from app.enums import UserRole
from app.models import User
from app.core.security import hash_password


@pytest.fixture(autouse=True)
def mock_db_commit():
    """Mock db.session.commit and db.session.remove to prevent SQLite savepoint invalidation during tests."""
    with patch("app.models.base.db.session.commit") as mock_commit, \
         patch("app.models.base.db.session.remove") as mock_remove:
        yield mock_commit


@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis token denylist consume to avoid connection errors in tests."""
    with patch("app.core.token_denylist.RedisTokenDenylist.consume", return_value=True) as mock_consume:
        yield mock_consume


@pytest.fixture
def test_user(db_session) -> User:
    """Seeded test agent user."""
    user = User(
        email="testagent@thrive.com",
        full_name="Test Agent User",
        password_hash=hash_password("Password123!"),
        role=UserRole.AGENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_login_endpoint_success(client, test_user, json_headers):
    payload = {
        "email": "testagent@thrive.com",
        "password": "Password123!",
    }
    resp = client.post(
        "/api/v1/auth/login",
        data=json.dumps(payload),
        headers=json_headers,
    )
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["email"] == "testagent@thrive.com"
    assert "Login successful." in res_data["message"]


def test_login_endpoint_invalid_credentials(client, test_user, json_headers):
    payload = {
        "email": "testagent@thrive.com",
        "password": "WrongPassword!",
    }
    resp = client.post(
        "/api/v1/auth/login",
        data=json.dumps(payload),
        headers=json_headers,
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    res_data = resp.get_json()
    assert res_data["error"] == "INVALID_CREDENTIALS"


def test_logout_endpoint_unauthenticated(client, json_headers):
    resp = client.post("/api/v1/auth/logout", headers=json_headers)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    res_data = resp.get_json()
    assert res_data["error"] == "AUTHENTICATION_ERROR"


def test_logout_endpoint_success(client, test_user, json_headers):
    # Log in first to set session cookie
    client.post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": "testagent@thrive.com",
            "password": "Password123!",
        }),
        headers=json_headers,
    )
    # Log out
    resp = client.post("/api/v1/auth/logout", headers=json_headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT


def test_change_password_endpoint_success(client, test_user, json_headers):
    # Log in first
    client.post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": "testagent@thrive.com",
            "password": "Password123!",
        }),
        headers=json_headers,
    )
    # Change password
    payload = {
        "current_password": "Password123!",
        "new_password": "NewPassword123!",
        "confirm_password": "NewPassword123!",
    }
    resp = client.post(
        "/api/v1/auth/change-password",
        data=json.dumps(payload),
        headers=json_headers,
    )
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert "Password changed successfully." in res_data["message"]


def test_forgot_password_endpoint_success(client, test_user, json_headers):
    payload = {
        "email": "testagent@thrive.com",
    }
    resp = client.post(
        "/api/v1/auth/forgot-password",
        data=json.dumps(payload),
        headers=json_headers,
    )
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert "If that email is registered" in res_data["message"]


@patch("app.interface.auth.services.verify_reset_token", return_value="user-abc-123")
def test_reset_password_endpoint_success(mock_verify, client, test_user, json_headers):
    # Mock user retrieval inside reset password operation
    with patch("app.repository.user.UserRepository.get", return_value=test_user):
        payload = {
            "token": "valid-token-value",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }
        resp = client.post(
            "/api/v1/auth/reset-password",
            data=json.dumps(payload),
            headers=json_headers,
        )
        assert resp.status_code == HTTPStatus.OK
        res_data = resp.get_json()
        assert res_data["success"] is True
        assert "Password has been reset." in res_data["message"]


def test_mfa_enroll_endpoint_unauthenticated(client, json_headers):
    resp = client.post("/api/v1/auth/mfa/enroll", headers=json_headers)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_mfa_enroll_endpoint_success(client, test_user, json_headers):
    # Log in first
    client.post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": "testagent@thrive.com",
            "password": "Password123!",
        }),
        headers=json_headers,
    )
    # Enroll MFA
    resp = client.post("/api/v1/auth/mfa/enroll", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert "provisioning_uri" in res_data["data"]
    assert "qr_code_data_url" in res_data["data"]


def test_rate_limit_exceeded_error_handling(client, json_headers):
    from flask_limiter.errors import RateLimitExceeded
    limit_mock = MagicMock()
    limit_mock.error_message = "10 per 1 minute"
    with patch("app.api.v1.auth.routes.routes.LoginView.post", side_effect=RateLimitExceeded(limit_mock)):
        resp = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"email": "test@thrive.com", "password": "wrong"}),
            headers=json_headers,
        )
        assert resp.status_code == HTTPStatus.TOO_MANY_REQUESTS
        res_data = resp.get_json()
        assert res_data["error"] == "RATE_LIMIT_EXCEEDED"
        assert res_data["message"] == "Too many requests. Please try again later."


def test_login_account_locked_returns_401(client, test_user, json_headers):
    from datetime import datetime, timezone, timedelta
    test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    payload = {
        "email": test_user.email,
        "password": "Password123!",
    }
    resp = client.post(
        "/api/v1/auth/login",
        data=json.dumps(payload),
        headers=json_headers,
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    res_data = resp.get_json()
    assert res_data["error"] == "ACCOUNT_INACTIVE"
    assert "locked" in res_data["message"]


# ── Integration Tests: User Self-Registration & Google OAuth ─────────────────

def test_register_agent_success(client, db_session, json_headers):
    payload = {
        "full_name": "Self Registered Agent",
        "email": "selfregistered@thrive.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "phone": "+1234567890",
    }
    
    with patch("app.interface.auth.services.event_bus") as mock_bus:
        resp = client.post(
            "/api/v1/auth/register",
            data=json.dumps(payload),
            headers=json_headers,
        )
    assert resp.status_code == HTTPStatus.CREATED
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["email"] == "selfregistered@thrive.com"
    assert res_data["data"]["role"] == "agent"


def test_register_agent_duplicate_email(client, db_session, test_user, json_headers):
    payload = {
        "full_name": "Self Registered Agent",
        "email": test_user.email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    resp = client.post(
        "/api/v1/auth/register",
        data=json.dumps(payload),
        headers=json_headers,
    )
    assert resp.status_code == HTTPStatus.CONFLICT
    res_data = resp.get_json()
    assert res_data["error"] == "DUPLICATE_EMAIL"


def test_register_agent_passwords_mismatch(client, json_headers):
    payload = {
        "full_name": "Self Registered Agent",
        "email": "mismatch@thrive.com",
        "password": "Password123!",
        "confirm_password": "PasswordMismatch!",
    }
    resp = client.post(
        "/api/v1/auth/register",
        data=json.dumps(payload),
        headers=json_headers,
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_google_login_redirect(client):
    from app.core.config import settings
    with patch.object(settings, "GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(settings, "GOOGLE_CLIENT_SECRET", "test-client-secret"), \
         patch.object(settings, "GOOGLE_REDIRECT_URI", "http://localhost:5000/api/v1/auth/google/callback"), \
         patch("app.api.v1.auth.routes.routes.get_redis") as mock_redis_func:
        mock_redis = MagicMock()
        mock_redis_func.return_value = mock_redis
        
        resp = client.get("/api/v1/auth/google")
        assert resp.status_code == HTTPStatus.FOUND
        assert "accounts.google.com" in resp.headers["Location"]
        assert "client_id=test-client-id" in resp.headers["Location"]


def test_google_callback_invalid_state(client):
    with patch("app.api.v1.auth.routes.routes.get_redis") as mock_redis_func:
        mock_redis = MagicMock()
        mock_redis.exists.return_value = False
        mock_redis_func.return_value = mock_redis

        resp = client.get("/api/v1/auth/google/callback?code=foo&state=bar")
        assert resp.status_code == HTTPStatus.FOUND
        assert "status=error" in resp.headers["Location"]
        assert "Invalid+state" in resp.headers["Location"]
        mock_redis.exists.assert_called_once_with("oauth_state:bar")


