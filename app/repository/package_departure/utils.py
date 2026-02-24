class CapacityExceededError(ValueError):
    """Raised when an attempt is made to reserve more capacity than mechanically exists."""
    pass

class ConcurrentUpdateError(Exception):
    """Raised when an optimistic lock (`version_id`) trap evaluates avoiding a race-condition collision."""
    pass
