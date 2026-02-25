from dataclasses import dataclass
from typing import Optional, List
from datetime import date

@dataclass
class TrackEventDTO:
    metric_name: str
    category: Optional[str] = None
    value: float = 0.0
    dimension_key: Optional[str] = None

@dataclass
class ReportFilterDTO:
    start_date: date
    end_date: date
    metric_names: Optional[List[str]] = None
