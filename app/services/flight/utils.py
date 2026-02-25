from typing import List
from app.dto.flight.schemas import FlightSegmentDTO

def calculate_total_duration(segments: List[FlightSegmentDTO]) -> int:
    """
    Safely sums duration bounds explicitly bypassing Nones or dynamically deriving
    the differential traversing the last arrival versus the first departure natively.
    """
    if not segments:
        return 0
        
    explicit_durations = [seg.duration_minutes for seg in segments if seg.duration_minutes is not None]
    if explicit_durations and len(explicit_durations) == len(segments):
         return sum(explicit_durations)
         
    # Derive chronologically if explicitly omitted
    ordered = sorted(segments, key=lambda x: x.departure_time)
    start = ordered[0].departure_time
    end = ordered[-1].arrival_time
    
    return int((end - start).total_seconds() / 60)
