from dataclasses import dataclass, field
from typing import Optional, List
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
@dataclass
class CreatePackageItineraryDTO:
    day_number: int 
    title: Optional[str]
    description: Optional[str]
    location: Optional[str]

@dataclass
class CreatePackageInclusionDTO:
    description: str
    is_included: bool = True

@dataclass
class CreatePackageMediaDTO:
    image_url: str
    display_order: Optional[int]
    is_featured: bool = False

@dataclass
class CreatePackageDTO:
    title: str 
    slug: Optional[str]
    description: Optional[str]
    highlights: Optional[List[str]]

    duration_nights: int
    duration_days: int

    country: Optional[str]
    city: Optional[str]

    meta_description: Optional[str]
    meta_title: Optional[str]

    currency: Optional[str] = "USD"

    is_active: Optional[bool] = True
    is_featured: Optional[bool] = False

    itineraries: Optional[List[CreatePackageItineraryDTO]] = field(default_factory=list)
    inclusions: Optional[List[CreatePackageInclusionDTO]] = field(default_factory=list)
    media: Optional[List[CreatePackageMediaDTO]] = field(default_factory=list)
