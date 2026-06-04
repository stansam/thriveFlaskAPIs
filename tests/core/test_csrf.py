"""
Unit and integration tests for CSRF protection.
"""
from __future__ import annotations

import pytest
from flask import Flask
from app.core.security.csrf import csrf_protect
from app.core.errors import register_error_handlers


def test_csrf_decorator_mutation_blocked_without_header():
    app = Flask("test_csrf_app")
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = True
    register_error_handlers(app)

    @app.route("/mutate", methods=["POST"])
    @csrf_protect
    def mutate():
        return {"status": "success"}

    with app.test_client() as client:
        # POST request without header should be rejected
        response = client.post("/mutate")
        assert response.status_code == 401
        assert response.get_json()["error"] == "AUTHENTICATION_ERROR"


def test_csrf_decorator_mutation_allowed_with_header():
    app = Flask("test_csrf_app")
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = True
    register_error_handlers(app)

    @app.route("/mutate", methods=["POST"])
    @csrf_protect
    def mutate():
        return {"status": "success"}

    with app.test_client() as client:
        # POST request with correct header should be allowed
        response = client.post("/mutate", headers={"X-Requested-With": "XMLHttpRequest"})
        assert response.status_code == 200
        assert response.get_json() == {"status": "success"}


def test_csrf_decorator_safe_method_allowed_without_header():
    app = Flask("test_csrf_app")
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = True
    register_error_handlers(app)

    @app.route("/safe", methods=["GET"])
    @csrf_protect
    def safe():
        return {"status": "success"}

    with app.test_client() as client:
        # GET request should not be blocked even without the header
        response = client.get("/safe")
        assert response.status_code == 200
        assert response.get_json() == {"status": "success"}


def test_csrf_decorator_disabled_bypasses_check():
    app = Flask("test_csrf_app")
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disabled
    register_error_handlers(app)

    @app.route("/mutate", methods=["POST"])
    @csrf_protect
    def mutate():
        return {"status": "success"}

    with app.test_client() as client:
        # With CSRF disabled, POST without header should succeed
        response = client.post("/mutate")
        assert response.status_code == 200
        assert response.get_json() == {"status": "success"}


def test_csrf_cookie_setting_on_response(app):
    # Use app fixture from conftest, but temporarily enable CSRF
    original_csrf = app.config.get("WTF_CSRF_ENABLED")
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["SESSION_COOKIE_NAME"] = "thrive_session"

    try:
        with app.test_client() as client:
            response = client.get("/api/v1/users/me") # any endpoint
            cookie_name = "thrive_session_csrf"
            
            # Check if cookie was set in the response headers
            cookie_header = response.headers.get("Set-Cookie")
            assert cookie_header is not None
            assert f"{cookie_name}=" in cookie_header
            assert "SameSite=Lax" in cookie_header
    finally:
        app.config["WTF_CSRF_ENABLED"] = original_csrf
