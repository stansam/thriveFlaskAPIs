from typing import Dict, List
from pydantic import BaseModel
from app.repository.flight.structure import PriceDTO

class FilterStopsDTO(BaseModel):
    id: str
    items: Dict[int, FilterStopsItemDTO]

class FilterStopsItemDTO(BaseModel):
    checked: str
    count: int
    default_value: bool
    display_value: str
    id: str
    is_hide_only: bool
    only: bool
    price: List[PriceDTO]
    selected: bool
    show_all_state: bool
    unchecked: str
    