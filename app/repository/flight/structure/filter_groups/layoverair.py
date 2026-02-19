from typing import Dict, List
from pydantic import BaseModel
from app.repository.flight.structure import PriceDTO

class FilterLayOverAirDTO(BaseModel):
    id: str
    items: Dict[int, FilterLayOverAirItemDTO]

class FilterLayOverAirItemDTO(BaseModel):
    checked: str
    count: int
    default_value: bool
    disabled: bool
    display_value: str
    id: str
    is_disabled: bool
    is_hide_only: bool
    only: bool
    parent_id: str
    selected: bool
    show_all_state: bool
    unchecked: str
    