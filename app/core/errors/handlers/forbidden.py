from app.core.errors.handlers.base import AppError
from http import HTTPStatus

class PermissionDeniedError(AppError):
    http_status = HTTPStatus.FORBIDDEN
    error_code  = "PERMISSION_DENIED"

    def __init__(self, message: str = "You do not have permission to perform this action.", **kwargs):
        super().__init__(message, **kwargs)


class InsufficientRoleError(PermissionDeniedError):
    error_code = "INSUFFICIENT_ROLE"

    def __init__(self, required_role: str = "", **kwargs):
        msg = (
            f"This action requires the '{required_role}' role."
            if required_role
            else "Insufficient role permissions."
        )
        super().__init__(msg, **kwargs)


