from datetime import date, datetime

def normalize_metric_name(name: str) -> str:
    """Consistently lowercases metric identifiers for safe grouping aggregations."""
    if not name:
        return ""
    return str(name).strip().lower()

def normalize_date(date_dimension) -> date:
    """
    Date dimension truncation utilities. Ensures all events correctly truncate their timestamp 
    (stripping hours/minutes/seconds) to align reliably on unified `date` blocks locally.
    """
    if isinstance(date_dimension, datetime):
        return date_dimension.date()
    elif isinstance(date_dimension, str):
        try:
            return datetime.strptime(date_dimension.split('T')[0], '%Y-%m-%d').date()
        except ValueError:
            return date.today()
    elif isinstance(date_dimension, date):
        return date_dimension
    
    # Failsafe fallback
    return date.today()
