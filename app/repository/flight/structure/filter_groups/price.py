from typing import Dict, List
from pydantic import BaseModel
from app.repository.flight.structure import PriceDTO

class FilterPriceDTO(BaseModel):
    average_price: List[PriceDTO]
    count: Dict[int, int]
    formatted_values: Dict[int, str]
    left_range: int
    max_count: int
    max_range: int
    max_selected: int
    min_range: int
    min_selected: int
    right_range: int
    values: Dict[int, int]
    