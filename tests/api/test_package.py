"""
Integration tests for Package API endpoints.
"""
from __future__ import annotations

import json
import io
from unittest.mock import patch, MagicMock
from http import HTTPStatus
import pytest

from app.enums import UserRole, PackageStatus, InclusionType, AssetType
from app.models import User, TravelPackage
from app.core.security import hash_password


@pytest.fixture(autouse=True)
def mock_db_commit():
    """Mock db.session.commit and db.session.remove to prevent SQLite savepoint invalidation during tests."""
    with patch("app.models.base.db.session.commit") as mock_commit, \
         patch("app.models.base.db.session.remove") as mock_remove:
        yield mock_commit


@pytest.fixture
def admin_user(db_session) -> User:
    """Seeded test admin user."""
    user = User(
        email="admin@test.thrive.com",
        full_name="Test Admin User",
        password_hash=hash_password("AdminPass1!"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def agent_user(db_session) -> User:
    """Seeded test agent user."""
    user = User(
        email="agent@test.thrive.com",
        full_name="Test Agent User",
        password_hash=hash_password("AgentPass1!"),
        role=UserRole.AGENT,
        is_active=True,
    )
    db_session.add(user)
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


def _login_admin(client, json_headers) -> None:
    _login_as(client, "admin@test.thrive.com", "AdminPass1!", json_headers)


def _login_agent(client, json_headers) -> None:
    _login_as(client, "agent@test.thrive.com", "AgentPass1!", json_headers)


def test_get_packages_unauthenticated(client, json_headers):
    resp = client.get("/api/v1/packages", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    res_data = resp.get_json()
    assert res_data["success"] is True
    assert isinstance(res_data["data"]["items"], list)


def test_get_packages_invalid_status_enum(client, json_headers):
    # Invalid status is caught by Marshmallow validation returning 422 Unprocessable Entity
    resp = client.get("/api/v1/packages?status=INVALID_STATUS", headers=json_headers)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    res_data = resp.get_json()
    assert res_data["error"] == "VALIDATION_ERROR"
    assert res_data["details"][0]["field"] == "status"


def test_create_package_unauthenticated(client, json_headers):
    payload = {
        "title": "Unauthenticated Package",
        "destination_country": "Kenya",
        "duration_days": 5,
        "duration_nights": 4,
        "base_price_usd": "1200.00"
    }
    resp = client.post(
        "/api/v1/packages",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_create_package_agent_forbidden(client, agent_user, json_headers):
    _login_agent(client, json_headers)
    payload = {
        "title": "Agent Package",
        "destination_country": "Kenya",
        "duration_days": 5,
        "duration_nights": 4,
        "base_price_usd": "1200.00"
    }
    resp = client.post(
        "/api/v1/packages",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_package_crud_lifecycle_admin_success(client, admin_user, json_headers):
    _login_admin(client, json_headers)

    # 1. Create Package
    payload = {
        "title": "Ultimate Kenya Safari",
        "destination_country": "Kenya",
        "duration_days": 5,
        "duration_nights": 4,
        "base_price_usd": "1200.00"
    }
    resp = client.post(
        "/api/v1/packages",
        data=json.dumps(payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.CREATED
    res_data = resp.get_json()
    assert res_data["success"] is True
    package_id = res_data["data"]["id"]
    slug = res_data["data"]["slug"]
    assert res_data["data"]["title"] == "Ultimate Kenya Safari"
    assert res_data["data"]["status"] == "draft"

    # 2. Get Package details
    resp = client.get(f"/api/v1/packages/{package_id}", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["title"] == "Ultimate Kenya Safari"

    # 3. Get Package by slug
    resp = client.get(f"/api/v1/packages/slug/{slug}", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["id"] == package_id

    # 4. Update Package
    update_payload = {
        "tagline": "A majestic adventure in East Africa"
    }
    resp = client.patch(
        f"/api/v1/packages/{package_id}",
        data=json.dumps(update_payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["tagline"] == "A majestic adventure in East Africa"

    # 5. Add Highlight
    hl_payload = {
        "text": "See the Big Five",
        "icon": "safari"
    }
    resp = client.post(
        f"/api/v1/packages/{package_id}/highlights",
        data=json.dumps(hl_payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.CREATED
    hl_id = resp.get_json()["data"]["id"]

    # 6. Add Itinerary Day
    it_payload = {
        "day_number": 1,
        "title": "Arrival in Nairobi",
        "description": "Welcome to Kenya!"
    }
    resp = client.post(
        f"/api/v1/packages/{package_id}/itinerary",
        data=json.dumps(it_payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.CREATED
    day_id = resp.get_json()["data"]["id"]

    # 7. Add Price Tier
    tier_payload = {
        "label": "Base Tier",
        "price_usd": "1200.00",
        "min_participants": 1,
        "max_participants": 4
    }
    resp = client.post(
        f"/api/v1/packages/{package_id}/price-tiers",
        data=json.dumps(tier_payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.CREATED
    tier_id = resp.get_json()["data"]["id"]

    # 8. Resolve Price
    resp = client.get(
        f"/api/v1/packages/{package_id}/resolve-price?num_participants=2",
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()["data"]["resolved_price_usd"] == "2400.00"

    # 9. Add Insurance Option
    ins_payload = {
        "provider_name": "Allianz",
        "policy_name": "Gold Travel Protection",
        "premium_usd": "50.00",
        "per_person_rate": "15.00",
        "is_active": True
    }
    resp = client.post(
        f"/api/v1/packages/{package_id}/insurance",
        data=json.dumps(ins_payload),
        headers=json_headers
    )
    assert resp.status_code == HTTPStatus.CREATED
    ins_id = resp.get_json()["data"]["id"]

    # 10. List Insurance
    resp = client.get(f"/api/v1/packages/{package_id}/insurance", headers=json_headers)
    assert resp.status_code == HTTPStatus.OK
    assert len(resp.get_json()["data"]) == 1

    # 11. Delete Insurance
    resp = client.delete(f"/api/v1/packages/{package_id}/insurance/{ins_id}", headers=json_headers)
    assert resp.status_code == HTTPStatus.NO_CONTENT


def test_media_upload_invalid_enum(client, admin_user, json_headers):
    _login_admin(client, json_headers)
    
    package_id = "test-pkg-123"

    resp = client.post(
        f"/api/v1/packages/{package_id}/media/upload",
        data={
            "file": (io.BytesIO(b"fake image data"), "test.txt"),
            "alt_text": "Invalid asset type"
        },
        content_type="multipart/form-data"
    )
    
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid content type" in resp.get_json()["message"]
