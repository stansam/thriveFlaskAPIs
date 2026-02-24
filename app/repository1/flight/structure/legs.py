from pydantic import BaseModel
from typing import List, Dict

class LegsDTO(BaseModel):
    arrival: str # Format: YYYY-MM-DDTHH:MM:SS
    departure: str # Format: YYYY-MM-DDTHH:MM:SS
    duration: int
    segments: Dict[int, SegmentsDTO]

class SegmentsDTO(BaseModel):
    id: str
    layover: List[LayoverDTO]

class LayoverDTO(BaseModel):
    duration: int
    is_long: bool
    is_short: bool
    