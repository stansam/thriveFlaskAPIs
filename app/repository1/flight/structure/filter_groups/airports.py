from pydantic import BaseModel
from typing import List
from app.repository.flight.structure import PriceDTO

class FilterAirportsDTO(BaseModel):
    filter_groups: Dict[int, AirportFilterGroupDTO] 

class AirportFilterGroupDTO(BaseModel):
    filter_data: List[AirportFilterDataDTO] = []
    id: str
    
class AirportFilterDataDTO(BaseModel):
    combine_using: str
    filter_groups: Dict[int, AirportFilterDataGroupDTO] 
    id: str

class AirportFilterDataGroupDTO(BaseModel):
    filter_data: Dict[int, AirportFilterDataGroupDataDTO] 
    id: str

class AirportFilterDataGroupDataDTO(BaseModel):
    items: Dict[int, AirportFilterItemDTO] 
    id: str

class AirportFilterItemDTO(BaseModel):
    checked: str
    count: int
    default_value: bool
    display_value: str
    id: str
    is_hide_only: bool
    only: bool
    price: List[PriceDTO]
    selected: bool
    show_all_state: bool
    unchecked: str
