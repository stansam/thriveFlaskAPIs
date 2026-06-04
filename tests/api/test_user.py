"""
Integration tests for User API endpoints.
"""
from __future__ import annotations

import json
from unittest.mock import patch
from http import HTTPStatus
import pytest

from app.enums import UserRole
from app.models import User, UserPreference
from app.core.security import hash_password


@pytest.fixture(autouse=True)
def mock_db_commit():
    """Mock db.session.commit and db.session.remove to prevent SQLite savepoint invalidation during tests."""
    with patch("app.models.base.db.session.commit") as mock_commit, \
         patch("app.models.base.db.session.remove") as mock_remove:
        yield mock_commit


@pytest.fixture
def agent_user(db_session) -> User:
    """Seeded test agent user."""
    user = User(
        email="agent@thrive.com",
        full_name="Test Agent User",
        password_hash=hash_password("Password123!"),
        role=UserRole.AGENT,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Seed preference row
    pref = UserPreference(user_id=user.id)
    db_session.add(pref)
    db_session.flush()

    return user


def _login_as(client, email: str, password: str, json_headers: dict) -> None:
    """Helper: log in as a user and store session cookie."""
    resp = client.post(
        "/api/v1/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers=json_headers,
    )
    assert resp.status_code == HTTPStatus.OK, f"Login failed: {resp.get_json()}"


def _login_agent(client, json_headers) -> None:
    _login_as(client, "agent@thrive.com", "Password123!", json_headers)


def _login_admin(client, json_headers) -> None:
    _login_as(client, "admin@test.thrive.com", "AdminPass1!", json_headers)


# ── Existing Lockout Visibility Tests ─────────────────────────────────────────

def test_me_endpoint_excludes_lockout_fields(client, agent_user, json_headers):
    # Log in as agent
    _login_agent(client, json_headers)

    # Call /me endpoint
    resp = client.get("/api/v1/users/me", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    
    user_data = res_data["data"]
    assert "email" in user_data
    # Excludes lockout fields
    assert "failed_login_count" not in user_data
    assert "locked_until" not in user_data


def test_user_detail_endpoint_excludes_lockout_fields_for_self(client, agent_user, json_headers):
    # Log in as agent
    _login_agent(client, json_headers)

    # Call detail endpoint for self
    resp = client.get(f"/api/v1/users/{agent_user.id}", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    
    user_data = res_data["data"]
    assert "email" in user_data
    assert "failed_login_count" not in user_data
    assert "locked_until" not in user_data


def test_user_detail_endpoint_includes_lockout_fields_for_admin(client, agent_user, admin_user, json_headers):
    # Log in as admin
    _login_admin(client, json_headers)

    # Call detail endpoint for agent_user
    resp = client.get(f"/api/v1/users/{agent_user.id}", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    
    user_data = res_data["data"]
    assert "email" in user_data
    # Includes lockout fields
    assert "failed_login_count" in user_data
    assert "locked_until" in user_data


def test_user_list_endpoint_includes_lockout_fields_for_admin(client, agent_user, admin_user, json_headers):
    # Log in as admin
    _login_admin(client, json_headers)

    # Call list endpoint
    resp = client.get("/api/v1/users/", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    
    items = res_data["data"]
    assert len(items) > 0
    # Includes lockout fields on item
    assert "failed_login_count" in items[0]
    assert "locked_until" in items[0]


# ── Group A: GET /api/v1/users/ — List Users ───────────────────────────────────

def test_list_users_admin_success(client, agent_user, admin_user, json_headers):
    _login_admin(client, json_headers)
    resp = client.get("/api/v1/users/", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert isinstance(res_data["data"], list)


def test_list_users_agent_forbidden(client, agent_user, json_headers):
    _login_agent(client, json_headers)
    resp = client.get("/api/v1/users/", headers=json_headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN
    assert resp.get_json()["error"] == "INSUFFICIENT_ROLE"


def test_list_users_unauthenticated(client):
    resp = client.get("/api/v1/users/")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert resp.get_json()["error"] == "AUTHENTICATION_ERROR"


# ── Group B: POST /api/v1/users/ — Create User ─────────────────────────────────

def test_create_user_admin_success(client, admin_user, json_headers):
    _login_admin(client, json_headers)
    payload = {
        "email": "new_created@thrive.com",
        "full_name": "New Created Agent",
        "phone": "+12065550100",
        "password": "Password123!",
        "role": "agent"
    }
    resp = client.post(
        "/api/v1/users/",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.CREATED
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["email"] == "new_created@thrive.com"
    assert res_data["data"]["role"] == "agent"


def test_create_user_duplicate_email(client, agent_user, admin_user, json_headers):
    _login_admin(client, json_headers)
    payload = {
        "email": "agent@thrive.com",
        "full_name": "Duplicate Agent",
        "password": "Password123!",
        "role": "agent"
    }
    resp = client.post(
        "/api/v1/users/",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.CONFLICT
    assert resp.get_json()["error"] == "DUPLICATE_EMAIL"


def test_create_user_invalid_payload(client, admin_user, json_headers):
    _login_admin(client, json_headers)
    payload = {
        "full_name": "Invalid Agent",
        "password": "Password123!",
    }
    resp = client.post(
        "/api/v1/users/",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_user_agent_forbidden(client, agent_user, json_headers):
    _login_agent(client, json_headers)
    payload = {
        "email": "forbidden_agent@thrive.com",
        "full_name": "Forbidden Agent",
        "password": "Password123!",
    }
    resp = client.post(
        "/api/v1/users/",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_create_user_wrong_content_type(client, admin_user):
    headers = {"Content-Type": "text/plain"}
    json_headers = {"Content-Type": "application/json"}
    _login_admin(client, json_headers)

    payload = {
        "email": "wrong_ct@thrive.com",
        "full_name": "Wrong CT Agent",
        "password": "Password123!",
    }
    resp = client.post(
        "/api/v1/users/",
        data=json.dumps(payload),
        headers=headers
    )
    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE



# ── Group C: GET /api/v1/users/me — Get Own Profile ───────────────────────────

def test_get_me_authenticated(client, agent_user, json_headers):
    _login_agent(client, json_headers)
    resp = client.get("/api/v1/users/me", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert res_data["data"]["email"] == "agent@thrive.com"


def test_get_me_unauthenticated(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


# ── Group D: GET /api/v1/users/<user_id> — Get User Detail ─────────────────────

def test_get_user_self_success(client, agent_user, json_headers):
    _login_agent(client, json_headers)
    resp = client.get(f"/api/v1/users/{agent_user.id}", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["email"] == "agent@thrive.com"


def test_get_user_admin_any_user(client, agent_user, admin_user, json_headers):
    _login_admin(client, json_headers)
    resp = client.get(f"/api/v1/users/{agent_user.id}", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK


def test_get_user_agent_other_user_forbidden(client, agent_user, admin_user, json_headers):
    _login_agent(client, json_headers)
    resp = client.get(f"/api/v1/users/{admin_user.id}", headers=json_headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_get_user_not_found(client, admin_user, json_headers):
    _login_admin(client, json_headers)
    resp = client.get("/api/v1/users/non-existent-id", headers=json_headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND


# ── Group E: PATCH /api/v1/users/<user_id> — Update User ───────────────────────

def test_update_user_self_success(client, agent_user, json_headers):
    _login_agent(client, json_headers)
    payload = {"full_name": "Updated Agent Name"}
    resp = client.patch(
        f"/api/v1/users/{agent_user.id}",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["full_name"] == "Updated Agent Name"


def test_update_user_admin_success(client, agent_user, admin_user, json_headers):
    _login_admin(client, json_headers)
    payload = {"role": "read_only"}
    resp = client.patch(
        f"/api/v1/users/{agent_user.id}",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["role"] == "read_only"


def test_update_user_agent_other_forbidden(client, agent_user, admin_user, json_headers):
    _login_agent(client, json_headers)
    payload = {"full_name": "Trying to Hack Admin Name"}
    resp = client.patch(
        f"/api/v1/users/{admin_user.id}",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_update_user_unknown_fields_rejected(client, agent_user, json_headers):
    _login_agent(client, json_headers)
    payload = {"unknown_field": "some_value"}
    resp = client.patch(
        f"/api/v1/users/{agent_user.id}",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ── Group F: POST /api/v1/users/<user_id>/deactivate — Deactivate ──────────────

def test_deactivate_user_admin_success(client, agent_user, admin_user, json_headers):
    _login_admin(client, json_headers)
    resp = client.post(f"/api/v1/users/{agent_user.id}/deactivate", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["is_active"] is False


def test_deactivate_user_self_blocked(client, admin_user, json_headers):
    _login_admin(client, json_headers)
    resp = client.post(f"/api/v1/users/{admin_user.id}/deactivate", headers=json_headers)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_deactivate_user_agent_forbidden(client, agent_user, admin_user, json_headers):
    _login_agent(client, json_headers)
    resp = client.post(f"/api/v1/users/{agent_user.id}/deactivate", headers=json_headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


# ── Group G: POST /api/v1/users/<user_id>/reactivate — Reactivate ──────────────

def test_reactivate_user_admin_success(client, agent_user, admin_user, json_headers):
    _login_admin(client, json_headers)
    # Deactivate first
    client.post(f"/api/v1/users/{agent_user.id}/deactivate", headers=json_headers)
    # Reactivate
    resp = client.post(f"/api/v1/users/{agent_user.id}/reactivate", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["is_active"] is True


def test_reactivate_user_agent_forbidden(client, agent_user, admin_user, json_headers):
    _login_agent(client, json_headers)
    resp = client.post(f"/api/v1/users/{agent_user.id}/reactivate", headers=json_headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


# ── Group H: GET /api/v1/users/<user_id>/preferences — Get Preferences ─────────

def test_get_preferences_self_success(client, agent_user, json_headers):
    _login_agent(client, json_headers)
    resp = client.get(f"/api/v1/users/{agent_user.id}/preferences", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    assert "language" in resp.get_json()["data"]


def test_get_preferences_admin_any_user(client, agent_user, admin_user, json_headers):
    _login_admin(client, json_headers)
    resp = client.get(f"/api/v1/users/{agent_user.id}/preferences", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK


def test_get_preferences_agent_other_forbidden(client, agent_user, admin_user, json_headers):
    _login_agent(client, json_headers)
    resp = client.get(f"/api/v1/users/{admin_user.id}/preferences", headers=json_headers)
    assert resp.status_code == HTTPStatus.FORBIDDEN


# ── Group I: PATCH /api/v1/users/<user_id>/preferences — Update Preferences ────

def test_update_preferences_self_success(client, agent_user, json_headers):
    _login_agent(client, json_headers)
    payload = {"language": "sw", "theme": "dark"}
    resp = client.patch(
        f"/api/v1/users/{agent_user.id}/preferences",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["language"] == "sw"
    assert resp.get_json()["data"]["theme"] == "dark"


def test_update_preferences_agent_other_forbidden(client, agent_user, admin_user, json_headers):
    _login_agent(client, json_headers)
    payload = {"language": "sw"}
    resp = client.patch(
        f"/api/v1/users/{admin_user.id}/preferences",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN
