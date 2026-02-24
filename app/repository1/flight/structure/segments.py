from pydantic import BaseModel

class SegmentsDTO(BaseModel):
    airline: str
    arrival: str
    departure: str
    destination: str
    duration: int
    equipmentTypeName: str
    flightNumber: str
    origin: str