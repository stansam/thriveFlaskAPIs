"""
Integration tests for User API endpoints.
"""
from __future__ import annotations

import json
from unittest.mock import patch
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
    return user


def test_me_endpoint_excludes_lockout_fields(client, agent_user, json_headers):
    # Log in as agent
    client.post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": "agent@thrive.com",
            "password": "Password123!",
        }),
        headers=json_headers,
    )

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
    client.post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": "agent@thrive.com",
            "password": "Password123!",
        }),
        headers=json_headers,
    )

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
    client.post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": "admin@test.thrive.com",
            "password": "AdminPass1!",
        }),
        headers=json_headers,
    )

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
    client.post(
        "/api/v1/auth/login",
        data=json.dumps({
            "email": "admin@test.thrive.com",
            "password": "AdminPass1!",
        }),
        headers=json_headers,
    )

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
