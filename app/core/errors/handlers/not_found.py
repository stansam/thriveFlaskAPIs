from app.core.errors.handlers.base import AppError
from http import HTTPStatus

class NotFoundError(AppError):
    http_status = HTTPStatus.NOT_FOUND
    error_code  = "NOT_FOUND"

    def __init__(self, resource: str = "Resource", resource_id: str | None = None, **kwargs):
        msg = f"{resource} not found."
        if resource_id:
            msg = f"{resource} '{resource_id}' not found."
        super().__init__(msg, **kwargs)

