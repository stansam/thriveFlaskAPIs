from pydantic import BaseModel
from typing import List, Dict
from app.repository.flight.structure import UrlDTO

class SearchStatusDTO(BaseModel):
    bags: List[BagsDTO]
    can_display_price_prediction: bool
    cmp_2_data: List[Cmp2DataDTO]
    direct_flights_prechecked_preference: bool
    flex_mode: str
    is_contextual_search: bool
    is_country_search: bool
    is_government_search: bool
    is_multi_airport: bool
    is_open_flex: bool
    is_refundable_search: bool
    is_us_domestic_route: bool
    is_using_flex_dates: bool
    is_weekend: bool
    legs: Dict[int, LegsDTO]
    month_stay_nights: str
    social_meta: List[SocialMetaDTO]
    travelers: List[TravelersDTO]
    trip_type: str

class SocialMetaDTO(BaseModel):
    og_image_url: List[UrlDTO]
    twitter_image_url: List[UrlDTO]

class TravelersDTO(BaseModel):
    adults: int
    child: int
    lap_infant: int
    seat_infant: int
    seniors: int
    students: int
    youth: int
    
class BagsDTO(BaseModel):
    carry_on: int
    checked: int

class Cmp2DataDTO(BaseModel):
    data_type: str
    enabled: bool
    presentation: str

class LegsDTO(BaseModel):
    cabin: str
    date: str # Format: YYYY-MM-DD
    destination: List[DestinationDTO]
    flex_date: str
    origin: List[OriginDTO]

class DestinationDTO(BaseModel):
    is_nearby: bool
    locations: Dict[int, LegsLocationsDTO]

class LegsLocationsDTO(BaseModel):
    airport_code: str
    description: str
    display: str
    metro_for_codes: Dict[int, str]
    utc_offset: int


class OriginDTO(BaseModel):
    is_nearby: bool
    locations: Dict[int, OriginLocationsDTO]

class OriginLocationsDTO(BaseModel):
    airport_code: str
    description: str
    display: str
    utc_offset: int

