from typing import Dict
from pydantic import BaseModel

class FilterLayOverDurDTO(BaseModel):
    left_range: int
    max_range: int
    max_selected: int
    min_range: int
    min_selected: int
    right_range: int
    values: Dict[int, int]