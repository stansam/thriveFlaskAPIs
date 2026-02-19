from typing import List
from pydantic import BaseModel, Field
from app.repository.flight.structure.filter_data import FilterDataDTO
from app.repository.flight.structure.filtered_res_recommendation import FilteredResultsRecommendationDTO
from app.repository.flight.structure.legs import LegsDTO
from app.repository.flight.structure.providers import ProvidersDTO
from app.repository.flight.structure.results import ResultsDTO, ResultsStatisticsDTO
from app.repository.flight.structure.search_status import SearchStatusDTO
from app.repository.flight.structure.segments import SegmentsDTO
from app.repository.flight.structure.sort_data import SortDataDTO

class SearchFlightResponseDTO(BaseModel):
    data: List[DataDTO] = []
    error: str
    success: bool

class DataDTO(BaseModel):
    airlines: List[AirlinesDTO] = []
    airports: List[AirportsDTO] = []
    filter_data: List[FilterDataDTO] = []
    filtered_count: int
    filtered_results_recommendation: List[FilteredResultsRecommendationDTO] = []
    flight_alert_data: List[FlightAlertDataDTO] = []
    is_user_initiated: bool
    legs: Dict[str, LegsDTO]
    page_number: int
    page_size: int
    price_mode: str
    providers: Dict[str, ProvidersDTO]
    result_statistics: List[ResultsStatisticsDTO] = []
    results: Dict[int, ResultsDTO]
    search_id: str
    search_status: List[SearchStatusDTO] = []
    search_url: List[UrlDTO] = []
    segments: Dict[str, SegmentsDTO]
    sort_data: List[SortDataDTO] = []
    sort_mode: str
    status: str
    total_count: int

class AirlinesDTO(BaseModel):
    airline: Dict[str, AirlineDTO]

class AirlineDTO(BaseModel):
    airline_fee_url: list[Url] = []
    logo_url: list[Url] = []
    name: str = Field(min_length=1)

class UrlDTO(BaseModel):
    url: str
    url_type: str

class AirportsDTO(BaseModel):
    airports: Dict[str, AirportDTO]

class AirportDTO(BaseModel):
    city_code: str 
    city_name: str
    display_name: str
    full_display_name: str
   
class PriceDTO(BaseModel):
    currency: str
    localized_price: str
    price: float

class FlightAlertDataDTO(BaseModel):
    price_alert_enabled_for_query: bool

    
