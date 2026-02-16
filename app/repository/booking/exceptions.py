class BookingServiceException(Exception):
    """Base exception for Booking Service"""
    pass

class BookingNotFound(BookingServiceException):
    """Raised when a booking cannot be found"""
    pass

class PassengerNotFound(BookingServiceException):
    """Raised when a passenger cannot be found"""
    pass

class InvalidBookingStatus(BookingServiceException):
    """Raised when an invalid status transition is attempted"""
    pass

class DatabaseError(BookingServiceException):
    """Raised when a database operation fails"""
    pass

class BookingAlreadyExists(BookingServiceException):
    """Raised if a duplicate booking reference is generated (unlikely but possible)"""
    pass

class PaymentRequired(BookingServiceException):
    """Raised when an action requires a completed payment"""
    pass
