# app/api/v1/user/__init__.py
"""
User Blueprint definition.
"""
from flask import Blueprint

user_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")

from app.api.v1.user.routes import USER_ROUTES

for route in USER_ROUTES:
    user_bp.add_url_rule(
        rule=route["url_rule"],
        view_func=route["view_func"],
        methods=route["methods"],
    )

__all__ = ["user_bp"]
