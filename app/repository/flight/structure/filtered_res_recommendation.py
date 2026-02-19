from pydantic import BaseModel
from typing import List, Dict

class FilteredResultsRecommendationDTO(BaseModel):
    filters: List[RecommendationFilterDTO] = []
    nearby_airport_recommendation_info: List[NearbyAirportRecommendationInfoDTO] = []
    nearby_airport_view: bool

class RecommendationFilterDTO(BaseModel):
    airports: Dict[int, RecommendationAirportsDTO]
    cabin: Dict[int, RecommendationCabinDTO]
    show_52_longer_flights: Dict[int, Show52LongerFlightsDTO] 

class RecommendationAirportsDTO(BaseModel):
    filter_group: str
    is_only: bool
    name: str
    title: str
    value_set_item: bool

class RecommendationCabinDTO(BaseModel):
    filter_group: str
    is_only: bool
    name: str
    title: str
    value_set_item: bool

class Show52LongerFlightsDTO(BaseModel):
    filter_group: str
    is_only: bool
    name: str
    title: str
    value_set_item: bool

class NearbyAirportRecommendationInfoDTO(BaseModel):
    query_destination_code: str
    query_origin_code: str
    recommendation_code: str
    recommendation_distance: str
    recommendation_name: str
    recommendation_origin: bool
    
