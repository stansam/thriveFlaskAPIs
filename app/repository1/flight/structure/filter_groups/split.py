from typing import Dict, List
from pydantic import BaseModel

class FilterSplitDTO(BaseModel):
    id: str
    items: Dict[int, FilterSplitItemDTO]

class FilterSplitItemDTO(BaseModel):
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
    