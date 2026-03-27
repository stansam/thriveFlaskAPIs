from __future__ import annotations
from http import HTTPStatus

class AppError(Exception):
    """
    Root of the application exception hierarchy.

    Attributes
    ----------
    message     Human-readable description (safe to show to the end user).
    error_code  Machine-readable ALL_CAPS_SNAKE string (e.g. "NOT_FOUND").
    http_status HTTP response status code.
    details     Optional list of field-level error dicts.
    extra       Optional dict of additional context attached to the response.
    """

    http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code:  str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        *,
        details: list[dict[str, str]] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []
        self.extra = extra or {}

    def to_dict(self, request_id: str | None = None) -> dict:
        payload: dict[str, Any] = {
            "error":   self.error_code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        if request_id:
            payload["request_id"] = request_id
        if self.extra:
            payload.update(self.extra)
        return payload
