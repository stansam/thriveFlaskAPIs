from typing import Dict, List
from pydantic import BaseModel

class FilterPfcDTO(BaseModel):
    items: Dict[int, FilterPfcItemDTO]

class FilterPfcItemDTO(BaseModel):
    checked: str
    count: int
    default_value: bool
    display_value: str
    id: str
    is_hide_only: bool
    only: bool
    parent_id: str
    selected: bool
    show_all_state: bool
    unchecked: str
    