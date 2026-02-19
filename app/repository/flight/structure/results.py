from pydantic import BaseModel
from typing import List, Dict
from app.repository.flight.structure.url import UrlDTO

class ResultsStatisticsDTO(BaseModel):
    filtered_ads: int
    regular_flights: int
    total_raw_results: int

class ResultsDTO(BaseModel):
    ad_type: str
    button_text: str
    click_url: List[UrlDTO]
    company_name: str
    description: str
    headline: str
    index: int
    is_circle_ratings: bool
    is_sds: bool
    is_special_opaque: bool
    logo_url: List[UrlDTO]
    phone_number: str
    provider_code: str
    provider_name: str
    result_id: str
    seeker_provider: str
    show_payment_message: bool
    show_per_person_label: bool
    site: str
    track_url: List[UrlDTO]
    type: str