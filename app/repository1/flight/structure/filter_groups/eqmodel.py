from typing import Dict
from pydantic import BaseModel

class FilterEqModelDTO(BaseModel):
    items: Dict[int, FilterEqModelItemDTO]

class FilterEqModelItemDTO(BaseModel):
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



