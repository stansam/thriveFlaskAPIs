from typing import Dict
from pydantic import BaseModel

class FilterCfcDTO(BaseModel):
    items: Dict[int, FilterCfcItemDTO]

class FilterCfcItemDTO(BaseModel):
    checked: str
    count: int
    default_value: bool
    display_value: str
    id: str
    only: bool
    selected: bool
    unchecked: str



