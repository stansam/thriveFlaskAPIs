from typing import List 
from enum import Enum

class PassengersCodes(str, Enum):
    ADULT = "ADT" 
    SENIOR = "SNR" 
    STUDENT = "STD" 
    YOUTH = "YTH" 
    CHILD = "CHD" 
    TODDLER = "INS" 
    INFANT = "INL" 

class CabinClassesCodes(str, Enum):
    ECONOMY = "e"
    PREMIUM_ECONOMY = "p"
    BUSINESS = "b"
    FIRST = "f"

class SortOptions(str, Enum):
    PRICE_ASC = "price_a"
    DURATION_ASC = "duration_a"
    BEST_FLIGHT = "bestflight_a"
    EARLIEST_ARRIVAL = "arrival_a"

class FlightSearchRequestDTO(BaseModel):
    origin: str
    destination: str
    departure_date: str # Format: YYYY-MM-DD 
    # Optional Params
    return_date: Optional[str] = None # Format: YYYY-MM-DD
    filterParams: Optional[List[RequestFilterParamsDTO]] = None
    searchMetadata: Optional[List[SearchMetadataDTO]] = None
    userSearchParams: Optional[List[UserSearchParamsDTO]] = None

# API NOTE: Cabin filtering via API is not 100% reliable. It's better to filter results client-side.
class RequestFilterParamsDTO(BaseModel):
    fs: Optional[str] = Field(None,
     description="Raw Filter String i.e, 'fs': 'airlines=-OS;stops=0;price=-500;alliance=STAR_ALLIANCE'") # Check FilterFS for more combine options

class SearchMetadataDTO(BaseModel):
    pageNumber: Optional[int] = 1

class UserSearchParamsDTO(BaseModel):
    passengers: List[PassengersCodes] = None
    sortMode: Optional[SortOptions] = None

class FilterFS(BaseModel):
    airlines: Optional[str] = None # CODE or -CODE(Excludes)
    airports: Optional[str] = None # CODE or -CODE(Excludes)
    stops: Optional[str] = None # 0, 1, 2, 3, 4
    price: Optional[str] = None # -MAX or MIN-MAX e.g, -500 (under 500) or 200-500
    legdur:optional[str] = None # DURATION: legdur=-MAX (minutes) e.g legdur=-600 (under 10hours)
    layoverdur: optional[str] = None # layoverdur=MIN- (minutes) e.g layoverdur=120- (min 2hours) 
    alliance: Optional[str] = None # NAME e.g. =STAR_ALLIANCE
    sameair: Optional[str] = None # sameair
    equipment: Optional[str] = None # TYPE i.e equipment=W (Wide-Body)
    wifi: Optional[str] = None # wifi