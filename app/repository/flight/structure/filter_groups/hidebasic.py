from typing import Dict
from pydantic import BaseModel

class FilterHideBasicDTO(BaseModel):
    items: Dict[int, FilterHideBasicItemDTO]

class FilterHideBasicItemDTO(BaseModel):
    checked: str
    count: int
    default_value: bool
    display_value: str
    id: str
    only: bool
    selected: bool
    unchecked: str



