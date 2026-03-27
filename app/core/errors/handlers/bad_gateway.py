from app.core.errors.handlers.base import AppError
from http import HTTPStatus

class ExternalServiceError(AppError):
    http_status = HTTPStatus.BAD_GATEWAY
    error_code  = "EXTERNAL_SERVICE_ERROR"

    def __init__(self, service: str = "External service", message: str | None = None, **kwargs):
        msg = message or f"{service} is unavailable or returned an error."
        super().__init__(msg, **kwargs)


class KayakAPIError(ExternalServiceError):
    error_code = "FLIGHT_SEARCH_ERROR"

    def __init__(self, **kwargs):
        super().__init__(service="Flight search service", **kwargs)
