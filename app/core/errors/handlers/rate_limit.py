from app.core.errors.handlers.base import AppError
from http import HTTPStatus

class RateLimitExceededError(AppError):
    http_status = 429
    error_code  = "RATE_LIMIT_EXCEEDED"

    def __init__(self, message: str = "Too many requests. Please try again later.", **kwargs):
        super().__init__(message, **kwargs)


class SubscriptionLimitError(RateLimitExceededError):
    error_code = "SUBSCRIPTION_LIMIT_REACHED"

    def __init__(self, **kwargs):
        super().__init__(
            "Booking limit for this subscription period has been reached.",
            **kwargs,
        )
