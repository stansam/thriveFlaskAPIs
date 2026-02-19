from pydantic import BaseModel
from app.repository.flight.structure import PriceDTO
from typing import List, Dict

class SortDataDTO(BaseModel):
    arrive_a: List[SortDataFormatDTO]
    arrive_b: List[SortDataFormatDTO]
    best_flight_a: List[SortDataFormatDTO]
    co2_a: List[SortDataFormatDTO]
    depart_a: List[SortDataFormatDTO]
    depart_b: List[SortDataFormatDTO]
    duration_a: List[SortDataFormatDTO]
    price_a: List[SortDataFormatDTO]

class SortDataFormatDTO(BaseModel):
    duration: str
    price: List[PriceDTO]