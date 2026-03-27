from app.core.errors.handlers.base import AppError
from http import HTTPStatus

class AuthenticationError(AppError):
    http_status = HTTPStatus.UNAUTHORIZED
    error_code  = "AUTHENTICATION_ERROR"

    def __init__(self, message: str = "Authentication required.", **kwargs):
        super().__init__(message, **kwargs)


class InvalidCredentialsError(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"

    def __init__(self, message: str = "Invalid email or password.", **kwargs):
        super().__init__(message, **kwargs)


class TokenExpiredError(AuthenticationError):
    error_code = "TOKEN_EXPIRED"

    def __init__(self, message: str = "Token has expired.", **kwargs):
        super().__init__(message, **kwargs)


class TokenInvalidError(AuthenticationError):
    error_code = "TOKEN_INVALID"

    def __init__(self, message: str = "Token is invalid.", **kwargs):
        super().__init__(message, **kwargs)


class TokenRevokedError(AuthenticationError):
    error_code = "TOKEN_REVOKED"

    def __init__(self, message: str = "Token has been revoked.", **kwargs):
        super().__init__(message, **kwargs)


class MFARequiredError(AuthenticationError):
    error_code = "MFA_REQUIRED"

    def __init__(self, message: str = "MFA code is required.", **kwargs):
        super().__init__(message, **kwargs)


class MFAInvalidError(AuthenticationError):
    error_code = "MFA_INVALID"

    def __init__(self, message: str = "MFA code is invalid or expired.", **kwargs):
        super().__init__(message, **kwargs)


class AccountInactiveError(AuthenticationError):
    error_code = "ACCOUNT_INACTIVE"

    def __init__(self, message: str = "Account is deactivated.", **kwargs):
        super().__init__(message, **kwargs)


class PasswordResetTokenInvalidError(AuthenticationError):
    error_code = "RESET_TOKEN_INVALID"

    def __init__(self, message: str = "Password reset token is invalid or expired.", **kwargs):
        super().__init__(message, **kwargs)

