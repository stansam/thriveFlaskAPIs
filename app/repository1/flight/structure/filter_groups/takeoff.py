from typing import Dict, List
from pydantic import BaseModel
from app.repository.flight.structure import PriceDTO

class FilterTakeOffDTO(BaseModel):
    combine_using: str
    items: Dict[int, FilterTakeOffItemDTO]

class FilterTakeOffItemDTO(BaseModel):
    average_price: List[PriceDTO]
    count: Dict[int, int]
    date: str # Format: YYYY-MM-DD
    filter_display: str
    formatted_values: Dict[int, str]
    left_range: int
    max_count: int
    max_price: List[PriceDTO]
    max_range: int
    max_selected: int
    min_range: int
    min_selected: int
    prices: Dict[int, int]
    right_range: int
    values: Dict[int, int]
    