from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass
class SearchPackageDTO:
    country: Optional[str] = None
    duration_days_min: Optional[int] = None
    duration_days_max: Optional[int] = None

@dataclass
class BookPackageDTO:
    user_id: str
    package_id: str
    start_date: date
    end_date: date
    number_of_adults: int = 1
    number_of_children: int = 0
    special_requests: Optional[str] = None
