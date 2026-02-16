class UserServiceException(Exception):
    pass

class UserNotFound(UserServiceException):
    pass

class UserAlreadyExists(UserServiceException):
    pass

class InvalidCredentials(UserServiceException):
    pass

class InvalidVerificationToken(UserServiceException):
    pass

class EmailAlreadyVerified(UserServiceException):
    pass

class EmailNotVerified(UserServiceException):
    pass

class PasswordMismatch(UserServiceException):
    pass

class DatabaseError(UserServiceException):
    pass

class UserCreationFailed(UserServiceException):
    pass

class AuthenticationError(UserServiceException):
    """Raised when authentication fails"""
    pass
