from flask import Blueprint, request, jsonify
from app.main import main_bp
from app.main.schemas.flight_search import FlightSearchSchema
from app.repository.flight.adapters.kayak import KayakFlightAdapter
from app.repository.flight.mapper import ResponseMapper
from app.repository.flight.exceptions import FlightServiceError
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

# Note: Ideally routes should be class-based views (MethodView) to match auth routes style, 
# but for simple search func-based is also fine. Let's stick to functional for now or switch 
# if consistency is strictly enforced. Looking at auth/routes/login.py, they use MethodView.
# Let's use MethodView for consistency.

from flask.views import MethodView

class FlightSearch(MethodView):
    def post(self):
        schema = FlightSearchSchema()
        try:
            # Validate input
            params = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        try:
            # Call Adapter
            adapter = KayakFlightAdapter()
            raw_response = adapter.search_flights(params)
            
            # Caching Strategy
            from app.utils.cache import cache
            import hashlib
            import json

            # Create a unique cache key based on params
            # We sort keys to ensure consistency
            param_string = json.dumps(params, sort_keys=True, default=str)
            cache_key = f"flight_search:{hashlib.md5(param_string.encode()).hexdigest()}"
            
            cached_results = cache.get(cache_key)
            if cached_results:
                logger.info(f"Returning cached results for {cache_key}")
                return jsonify({"results": cached_results}), 200

            # Normalize Response
            mapper = ResponseMapper()
            results = mapper.normalize_search_response(raw_response)
            
            # Cache the normalized results for 15 minutes
            cache.set(cache_key, results, timeout=900)
            
            return jsonify({"results": results}), 200
            
        except FlightServiceError as e:
            return jsonify({"message": str(e)}), 503
        except Exception as e:
            logger.error(f"Unexpected error in flight search: {e}", exc_info=True)
            return jsonify({"message": "An unexpected error occurred"}), 500

class FlightDetails(MethodView):
    def get(self, flight_id):
        # Retrieve optional query parameters (e.g., source source=kayak)
        params = request.args.to_dict()
        
        try:
            # We can instantiate FlightService with None dB session if purely external
            # but usually we pass db.session. Here it's fine.
            from app.extensions import db
            from app.repository.flight.services import FlightService
            
            service = FlightService(db.session)
            details = service.get_flight_details(flight_id, params)
            
            return jsonify(details), 200
            
        except FlightServiceError as e:
            return jsonify({"message": str(e)}), 503
        except Exception as e:
            logger.error(f"Error fetching details: {e}")
            return jsonify({"message": "Failed to fetch details"}), 500

main_bp.add_url_rule('/api/flight/search', view_func=FlightSearch.as_view('flight_search'))
main_bp.add_url_rule('/api/flight/details/<flight_id>', view_func=FlightDetails.as_view('flight_details'))
