class NotificationServiceException(Exception):
    """Base exception for Notification Service"""
    pass

class NotificationNotFound(NotificationServiceException):
    """Raised when a notification cannot be found"""
    pass

class DatabaseError(NotificationServiceException):
    """Raised when a database operation fails"""
    pass
