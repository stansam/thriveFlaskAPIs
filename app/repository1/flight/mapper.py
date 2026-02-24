from app.repository.flight.structure import SearchFlightResponseDTO
import logging

logger = logging.getLogger(__name__)

class ResponseMapper:
    def normalize_search_response(self, raw_response: dict) -> SearchFlightResponseDTO:
        try:
            structured_response = SearchFlightResponseDTO(**raw_response)
            return structured_response
        except Exception as e:
            logger.error(f"Error mapping Kayak response to SearchFlightResponseDTO: {e}")
            raise
