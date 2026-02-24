from typing import Dict, List
from pydantic import BaseModel
from app.repository.flight.structure import PriceDTO

class FilterLandingDTO(BaseModel):
    combine_using: str
    items: Dict[int, FilterLandingItemDTO]

class FilterLandingItemDTO(BaseModel):
    average_price: List[PriceDTO]
    count: Dict[int, int]
    date: str # format: YYYY-MM-DD
    filter_display: str
    formatted_values: Dict[int, int]
    left_range: int
    mac_count: int
    max_price: List[PriceDTO]
    min_price: List[PriceDTO]
    max_range: int
    max_selected: int
    min_range: int
    min_selected: int
    show_all_state: bool
    prices: Dict[int, int]
    right_range: int
    values: Dict[int, int]
    