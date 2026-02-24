from typing import List
from app.repository.flight.requestDTO import FilterFS

class FlightFilterMapper:
    @staticmethod
    def fs_string(filter_params: FilterFS) -> str:
        parts = []

        if filter_params.airlines is not None:
            parts.append(f"airlines={filter_params.airlines}")  
        if filter_params.airports is not None:        
            parts.append(f"airports={filter_params.airports}")
        if filter_params.stops is not None:        
            parts.append(f"stops={filter_params.stops}")
        if filter_params.price is not None:        
            parts.append(f"price={filter_params.price}")
        if filter_params.legdur is not None:        
            parts.append(f"legdur={filter_params.legdur}")
        if filter_params.layoverdur is not None:        
            parts.append(f"layoverdur={filter_params.layoverdur}")
        if filter_params.alliance is not None:        
            parts.append(f"alliance={filter_params.alliance}")
        if filter_params.sameair is not None:        
            parts.append(f"sameair={filter_params.sameair}")
        if filter_params.equipment is not None:        
            parts.append(f"equipment={filter_params.equipment}")
        if filter_params.wifi is not None:        
            parts.append(f"wifi={filter_params.wifi}")
        return ";".join(parts)
        