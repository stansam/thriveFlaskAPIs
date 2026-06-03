# core/errors.py
"""
Application exception hierarchy and Flask error handler registration.

Architecture
------------
All application errors inherit from `AppError`.  Each subclass maps to
an HTTP status code and a machine-readable `error` code string that the
front-end can branch on without parsing message text.

Error envelope
--------------
Every error response — including unhandled 500s and Pydantic validation
failures — returns the same JSON shape (mirrors `ErrorResponse` DTO):

    {
        "error":   "VALIDATION_ERROR",
        "message": "Request body failed validation.",
        "details": [{"field": "email", "message": "value is not a valid email"}],
        "request_id": "abc-123"   // from X-Request-ID header if present
    }

Registration
------------
Call `register_error_handlers(app)` once in the application factory.
It installs handlers for:
  - All `AppError` subclasses
  - Pydantic `ValidationError` (body parsing failures)
  - Werkzeug `HTTPException` (404, 405, etc. from Flask routing)
  - Bare `Exception` (catch-all 500 with sanitised message in production)

Logging
-------
5xx errors are logged at ERROR level with full tracebacks.
4xx errors are logged at WARNING level with no traceback.
"""

from __future__ import annotations
import logging
import traceback
from http import HTTPStatus

from flask import Flask, jsonify, request
from marshmallow import ValidationError as MarshmallowValidationError
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException
from app.core.errors.handlers.base import AppError
from app.core.config import settings

logger = logging.getLogger(__name__)

def _pydantic_errors_to_details(exc: ValidationError) -> list[dict[str, str]]:
    """Convert Pydantic v2 ValidationError into our FieldError list format."""
    details: list[dict[str, str]] = []
    for error in exc.errors(include_url=False):
        loc = error.get("loc", ())
        field = ".".join(str(p) for p in loc) if loc else "body"
        details.append({
            "field":   field,
            "message": error.get("msg", "Invalid value."),
            "type":    error.get("type", ""),
        })
    return details


# Flask error handler registration
def register_error_handlers(app: Flask) -> None:
    """
    Attach all error handlers to the Flask application instance.
    Call this once inside the application factory.
    """

    def _get_request_id() -> str | None:
        return request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")

    # 1. Application errors (AppError and all subclasses)
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        request_id = _get_request_id()
        if exc.http_status >= 500:
            logger.error(
                "AppError [%s] %s — %s",
                exc.error_code,
                exc.http_status,
                exc.message,
                exc_info=True,
            )
        else:
            logger.warning(
                "AppError [%s] %s — %s",
                exc.error_code,
                exc.http_status,
                exc.message,
            )
        response = jsonify(exc.to_dict(request_id=request_id))
        response.status_code = exc.http_status
        return response

    # 2. Pydantic ValidationError (body parsing in service layer)
    @app.errorhandler(ValidationError)
    def handle_pydantic_validation_error(exc: ValidationError):
        request_id = _get_request_id()
        details = _pydantic_errors_to_details(exc)
        logger.warning("Pydantic ValidationError: %d errors", len(details))
        payload = {
            "error":      "VALIDATION_ERROR",
            "message":    "Request body failed validation.",
            "details":    details,
        }
        if request_id:
            payload["request_id"] = request_id
        response = jsonify(payload)
        response.status_code = HTTPStatus.UNPROCESSABLE_ENTITY
        return response

    # 2.5 Marshmallow ValidationError (API layer validation)
    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_validation_error(exc: MarshmallowValidationError):
        request_id = _get_request_id()
        details = []
        for field, messages in exc.messages.items():
            field_name = str(field)
            if isinstance(messages, list):
                for m in messages:
                    details.append({
                        "field":   field_name,
                        "message": str(m),
                        "type":    "invalid_value",
                    })
            elif isinstance(messages, dict):
                for subfield, submsg in messages.items():
                    details.append({
                        "field":   f"{field_name}.{subfield}",
                        "message": str(submsg),
                        "type":    "invalid_value",
                    })
            else:
                details.append({
                    "field":   field_name,
                    "message": str(messages),
                    "type":    "invalid_value",
                })
        logger.warning("Marshmallow ValidationError: %d errors", len(details))
        payload = {
            "error":      "VALIDATION_ERROR",
            "message":    "Request payload failed validation.",
            "details":    details,
        }
        if request_id:
            payload["request_id"] = request_id
        response = jsonify(payload)
        response.status_code = HTTPStatus.UNPROCESSABLE_ENTITY
        return response

    # 3. Werkzeug HTTP exceptions (Flask routing — 404, 405, etc.)
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        request_id = _get_request_id()
        error_code = exc.name.upper().replace(" ", "_") if exc.name else "HTTP_ERROR"
        payload = {
            "error":   error_code,
            "message": exc.description or exc.name or "HTTP error.",
        }
        if request_id:
            payload["request_id"] = request_id
        response = jsonify(payload)
        response.status_code = exc.code or 500
        return response

    # 4. Catch-all for unhandled exceptions (500)
    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        request_id = _get_request_id()
        logger.error(
            "Unhandled exception on %s %s\n%s",
            request.method,
            request.path,
            traceback.format_exc(),
        )
        if settings.DEBUG:
            message = f"{type(exc).__name__}: {str(exc)}"
        else:
            message = "An internal server error occurred."

        payload = {
            "error":   "INTERNAL_ERROR",
            "message": message,
        }
        if request_id:
            payload["request_id"] = request_id
        response = jsonify(payload)
        response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        return response