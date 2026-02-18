class FinanceServiceException(Exception):
    """Base exception for Finance Service"""
    pass

class PaymentFailed(FinanceServiceException):
    """Raised when a payment processing fails"""
    pass

class InvoiceGenerationFailed(FinanceServiceException):
    """Raised when invoice generation fails"""
    pass

class DatabaseError(FinanceServiceException):
    """Raised when a database operation fails"""
    pass

class InvalidAmount(FinanceServiceException):
    """Raised when payment amount is invalid"""
    pass

FinanceServiceError = FinanceServiceException
