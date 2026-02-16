class PackageServiceException(Exception):
    """Base exception for Package Service"""
    pass

class PackageNotFound(PackageServiceException):
    """Raised when a package cannot be found"""
    pass

class DatabaseError(PackageServiceException):
    """Raised when a database operation fails"""
    pass

class InvalidPackageData(PackageServiceException):
    """Raised when package data is invalid"""
    pass
