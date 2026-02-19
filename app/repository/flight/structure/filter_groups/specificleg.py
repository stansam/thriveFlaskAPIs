from typing import Dict, List
from pydantic import BaseModel

class FilterSpecificLegDTO(BaseModel):
    items: Dict[int, FilterSpecificLegItemDTO]
    specific_leg: bool

class FilterSpecificLegItemDTO(BaseModel):
    checked: str
    count: int
    default_value: bool
    display_value: str
    id: str
    is_hide_only: bool
    only: bool
    selected: bool
    show_all_state: bool
    unchecked: str
    