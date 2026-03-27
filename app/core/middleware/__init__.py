# app/middleware.py
"""
Flask middleware — runs before/after every request.

Responsibilities
----------------
1. Request ID injection       — generate/propagate X-Request-ID header
2. Request timing             — measure and log response time
3. Structured request logging — log method, path, status, duration
4. Security headers           — HSTS, X-Frame-Options, CSP, etc.
5. DB session cleanup         — ensure no uncommitted writes leak across
                                requests (belt-and-suspenders with SQLAlchemy)

Registration
------------
Call `register_middleware(app)` once in the application factory.
"""

from __future__ import annotations

import logging
import time
import uuid

from flask import Flask, Request, Response, g, request

logger = logging.getLogger(__name__)

# Security headers applied to every response
_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options":    "nosniff",
    "X-Frame-Options":           "DENY",
    "X-XSS-Protection":          "1; mode=block",
    "Referrer-Policy":           "strict-origin-when-cross-origin",
    "Permissions-Policy":        "geolocation=(), microphone=(), camera=()",
}

# Content-Security-Policy (relaxed for dev; tighten per environment)
_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)


def register_middleware(app: Flask) -> None:
    """Attach all before/after request hooks to the Flask application."""

    # ------------------------------------------------------------------
    # Before every request
    # ------------------------------------------------------------------

    @app.before_request
    def _stamp_request_id() -> None:
        """
        Accept an incoming X-Request-ID (from API gateway / load balancer)
        or generate a fresh one.  Store it on Flask g for use in logs and
        error responses.
        """
        request_id = (
            request.headers.get("X-Request-ID")
            or request.headers.get("X-Correlation-ID")
            or uuid.uuid4().hex
        )
        g.request_id = request_id
        g.request_start = time.perf_counter()

    # ------------------------------------------------------------------
    # After every request
    # ------------------------------------------------------------------

    @app.after_request
    def _inject_response_headers(response: Response) -> Response:
        """Add request ID, timing, and security headers to every response."""

        # Request ID echo
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id

        # Response timing
        start = getattr(g, "request_start", None)
        if start is not None:
            elapsed_ms = (time.perf_counter() - start) * 1000
            response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"
        else:
            elapsed_ms = 0.0

        # Security headers (skip for OPTIONS preflight)
        if request.method != "OPTIONS":
            for header, value in _SECURITY_HEADERS.items():
                response.headers.setdefault(header, value)
            from app.core.config import settings
            if not settings.DEBUG:
                response.headers.setdefault("Content-Security-Policy", _CSP)
                response.headers.setdefault(
                    "Strict-Transport-Security",
                    "max-age=31536000; includeSubDomains",
                )

        # Structured request log
        _log_request(response, elapsed_ms)

        return response

    # ------------------------------------------------------------------
    # Teardown — ensure SQLAlchemy session is cleaned up
    # ------------------------------------------------------------------

    @app.teardown_appcontext
    def _remove_db_session(exc: BaseException | None = None) -> None:
        """
        Remove the scoped SQLAlchemy session at the end of every request.
        Flask-SQLAlchemy does this automatically, but an explicit teardown
        provides belt-and-suspenders safety and a clear audit point.
        """
        from app.models.base import db
        db.session.remove()
        if exc is not None:
            logger.debug("DB session removed after exception: %s", exc)


def _log_request(response: Response, elapsed_ms: float) -> None:
    """Emit a single structured log line per request."""
    status = response.status_code
    level = logging.INFO if status < 400 else (
        logging.WARNING if status < 500 else logging.ERROR
    )

    request_id = getattr(g, "request_id", "-")
    user_id    = getattr(getattr(g, "current_user", None), "id", "-")

    logger.log(
        level,
        "%s %s %d %.2fms rid=%s uid=%s ip=%s",
        request.method,
        request.path,
        status,
        elapsed_ms,
        request_id,
        user_id,
        request.remote_addr or "-",
    )