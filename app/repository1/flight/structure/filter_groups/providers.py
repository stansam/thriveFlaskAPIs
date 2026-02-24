from typing import Dict, List
from pydantic import BaseModel

class FilterProvidersDTO(BaseModel):
    id: str
    items: Dict[int, FilterProvidersItemDTO]

class FilterProvidersItemDTO(BaseModel):
    airline_codes: Dict[int, str]
    checked: str
    count: int
    default_value: bool
    display_value: str
    id: str
    is_hide_only: bool
    is_meta: bool
    only: bool
    selected: bool
    show_all_state: bool
    unchecked: str
    