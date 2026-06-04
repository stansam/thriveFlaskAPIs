from __future__ import annotations

from functools import wraps
from flask import request, current_app
from app.core.errors.handlers import AuthenticationError


def csrf_protect(f):
    """
    Decorator to protect mutation views from Cross-Site Request Forgery (CSRF).

    For state-changing HTTP methods (POST, PUT, PATCH, DELETE), verifies that
    the 'X-Requested-With' header is present and set to 'XMLHttpRequest'.

    If 'WTF_CSRF_ENABLED' is set to False in application configuration,
    the verification is bypassed (useful for tests).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Bypass if CSRF protection is disabled
        if not current_app.config.get("WTF_CSRF_ENABLED", True):
            return f(*args, **kwargs)

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            requested_with = request.headers.get("X-Requested-With")
            if requested_with != "XMLHttpRequest":
                raise AuthenticationError(
                    "CSRF verification failed: X-Requested-With header missing or invalid."
                )
        return f(*args, **kwargs)
    return decorated
