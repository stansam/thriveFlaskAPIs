from datetime import datetime, timedelta, timezone

def get_expiry_cutoff_date(days: int) -> datetime:
    """
    Calculates the exact future datetime cutoff point for finding subscriptions
    that expire within X days from the current execution time.
    """
    return datetime.now(timezone.utc) + timedelta(days=days)
