class FlightServiceException(Exception):
    """Base exception for Flight Service"""
    pass

class FlightNotFound(FlightServiceException):
    """Raised when a flight cannot be found"""
    pass

class SeatNotAvailable(FlightServiceException):
    """Raised when a seat is already reserved"""
    pass

class DatabaseError(FlightServiceException):
    """Raised when a database operation fails"""
    pass

class InvalidSearchCriteria(FlightServiceException):
    """Raised when search parameters are invalid"""
    pass
