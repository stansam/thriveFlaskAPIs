from typing import Dict
from pydantic import BaseModel

class FilterEquipmentDTO(BaseModel):
    items: Dict[int, FilterEquipmentItemDTO] = []

class FilterEquipmentItemDTO(BaseModel):
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



