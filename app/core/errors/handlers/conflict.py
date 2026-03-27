from app.core.errors.handlers.base import AppError
from http import HTTPStatus

class ConflictError(AppError):
    http_status = HTTPStatus.CONFLICT
    error_code  = "CONFLICT"

    def __init__(self, message: str = "Resource already exists.", **kwargs):
        super().__init__(message, **kwargs)


class DuplicateEmailError(ConflictError):
    error_code = "DUPLICATE_EMAIL"

    def __init__(self, email: str = "", **kwargs):
        msg = f"Email '{email}' is already registered." if email else "Email already registered."
        super().__init__(msg, **kwargs)


class DuplicateSlugError(ConflictError):
    error_code = "DUPLICATE_SLUG"


class SubscriptionAlreadyActiveError(ConflictError):
    error_code = "SUBSCRIPTION_ALREADY_ACTIVE"

    def __init__(self, **kwargs):
        super().__init__("A subscription is already active for this account.", **kwargs)

