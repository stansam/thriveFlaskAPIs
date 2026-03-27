from app.core.errors.handlers.base import AppError
from http import HTTPStatus

class ValidationError_(AppError):
    """
    Wrapper for Pydantic validation failures raised inside service code.
    (Named with trailing _ to avoid shadowing pydantic.ValidationError.)
    """
    http_status = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code  = "VALIDATION_ERROR"

    def __init__(self, message: str = "Validation failed.", details: list[dict] | None = None, **kwargs):
        super().__init__(message, details=details, **kwargs)

