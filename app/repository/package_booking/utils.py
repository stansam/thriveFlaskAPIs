from datetime import datetime, timedelta, timezone, date

def get_future_cutoff_date(days: int) -> date:
    """
    Consistently anchors threshold lookaheads for querying future
    package departure bookings cleanly against the DB structure.
    """
    return (datetime.now(timezone.utc) + timedelta(days=days)).date()
