# app/api/v1/package/__init__.py
"""
Package Blueprint definition.
"""
from flask import Blueprint

package_bp = Blueprint("package", __name__, url_prefix="/api/v1/packages")

from app.api.v1.package.routes import PACKAGE_ROUTES

for route in PACKAGE_ROUTES:
    package_bp.add_url_rule(
        rule=route["url_rule"],
        view_func=route["view_func"],
        methods=route["methods"],
    )

__all__ = ["package_bp"]
