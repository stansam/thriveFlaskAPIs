import calendar
from datetime import datetime

def calculate_period_end_date(start_date: datetime, months: int = 1) -> datetime:
    """
    Safely calculates the temporal interval ensuring strict 30-day (or calendar bound) extensions
    avoiding standard `timedelta` skew metrics explicitly across leap configurations natively.
    """
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    
    # Cap explicitly exactly to the literal end of month lengths natively mapped (e.g. Feb 28 bounds cleanly)
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return start_date.replace(year=year, month=month, day=day)
