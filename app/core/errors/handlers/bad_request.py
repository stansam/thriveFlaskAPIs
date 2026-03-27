from app.core.errors.handlers.base import AppError
from http import HTTPStatus

class BadRequestError(AppError):
    http_status = HTTPStatus.BAD_REQUEST
    error_code  = "BAD_REQUEST"

    def __init__(self, message: str = "Bad request.", **kwargs):
        super().__init__(message, **kwargs)


class InvalidStatusTransitionError(BadRequestError):
    error_code = "INVALID_STATUS_TRANSITION"


class BusinessRuleViolationError(BadRequestError):
    error_code = "BUSINESS_RULE_VIOLATION"


class InsufficientBalanceError(BadRequestError):
    error_code = "INSUFFICIENT_BALANCE"


class DuplicateReferralError(BadRequestError):
    error_code = "DUPLICATE_REFERRAL"
