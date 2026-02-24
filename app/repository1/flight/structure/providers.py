from pydantic import BaseModel
from typing import List, Dict
from app.repository.flight.structure import UrlDTO

class ProvidersDTO(BaseModel):
    display_name: str
    logo_urls: Dict[int, LogoUrlDTO]
    provider_quality_score: List[ProviderQualityScoreDTO]

class LogoUrlDTO(BaseModel):
    horizontal_image_url: List[UrlDTO]
    image_url: List[UrlDTO]
    name: str
    wide_horizontal_image_url: List[UrlDTO]

class ProviderQualityScoreDTO(BaseModel):
    badge_text: str
    badge_type: str
    description: str