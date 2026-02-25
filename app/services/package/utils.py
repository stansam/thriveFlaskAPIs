from datetime import date, datetime
from typing import Dict
from app.dto.package.schemas import SearchPackageDTO

def build_package_search_filters(filters: SearchPackageDTO) -> Dict:
    """
    Strips raw DTO filters mapped into SQLAlchemy clean kwargs stripping None values.
    """
    clean_filters = {}
    if filters.country:
        clean_filters["country"] = filters.country
        
    # More advanced numerical inequalities (e.g., duration_days >= X) usually require explicit
    # .filter(Package.duration_days >= X) blocks outside standard generic dict maps.
    # For kwargs filtering `.filter_by()`, we stick to exact matches for now.
    return clean_filters

def validate_package_duration(start, end, required_days: int) -> None:
    """
    Asserts exact matching bounds natively against the physical Package length stopping
    users from truncating or expanding package dates against the listed configurations implicitly.
    """
    if isinstance(start, str):
        start = datetime.fromisoformat(start).date()
    elif hasattr(start, 'date'):
        start = start.date()
        
    if isinstance(end, str):
        end = datetime.fromisoformat(end).date()
    elif hasattr(end, 'date'):
        end = end.date()

    diff = (end - start).days
    
    # +1 because booking Monday through Wednesday implies 3 structural days of activity.
    actual_days = diff + 1 
    
    if actual_days != required_days:
        raise ValueError(f"Booking date range ({actual_days} days) does not match the strict Package definition requirement ({required_days} days).")
