from app.repository.flight.adapters.kayak import KayakFlightAdapter
from app.repository.flight.mapper import ResponseMapper
from app.utils.cache import cache
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class SearchFlights:
    def execute(self, params: dict) -> list[dict]:
        # Cache Strategy
        # Sort keys to ensure consistency
        param_string = json.dumps(params, sort_keys=True, default=str)
        cache_key = f"flight_search:{hashlib.md5(param_string.encode()).hexdigest()}"
        
        cached_results = cache.get(cache_key)
        if cached_results:
            logger.info(f"Returning cached results for {cache_key}")
            return cached_results

        # Call Adapter
        adapter = KayakFlightAdapter()
        raw_response = adapter.search_flights(params)
        
        # Normalize
        mapper = ResponseMapper()
        results = mapper.normalize_search_response(raw_response)
        
        # Cache
        cache.set(cache_key, results, timeout=900)
        
        return results
