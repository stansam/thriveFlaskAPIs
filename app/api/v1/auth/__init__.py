# app/api/v1/auth/__init__.py
"""
Auth Blueprint definition.
"""
from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

from app.api.v1.auth.routes import AUTH_ROUTES

for route in AUTH_ROUTES:
    auth_bp.add_url_rule(
        rule=route["url_rule"],
        view_func=route["view_func"],
        methods=route["methods"],
    )

__all__ = ["auth_bp"]
