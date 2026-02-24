from app.repository.flight.structure import UrlDTO, PriceDTO
from typing import List
from pydantic import BaseModel


class FilterAirlinesDTO(BaseModel):
    items: List[FilterAirlinesItemDTO] = [] 

class FilterAirlinesItemDTO(BaseModel):
    checked: str
    count: int
    default_value: bool
    display_value: str
    id: str
    is_hide_only: bool
    is_meta: bool
    logo_url: List[UrlDTO]
    multi: bool
    only: bool
    preference_disabled: bool
    price: List[PriceDTO]
    selected: bool
    show_all_state: bool
    unchecked: str
