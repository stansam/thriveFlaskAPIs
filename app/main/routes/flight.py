from flask import Blueprint, request, jsonify
from app.main import main_bp
from app.main.schemas.flight_search import FlightSearchSchema
from app.repository.flight.exceptions import FlightServiceError
from marshmallow import ValidationError
import logging
from flask.views import MethodView

logger = logging.getLogger(__name__)

class FlightSearch(MethodView):
    def post(self):
        schema = FlightSearchSchema()
        try:
            # Validate input
            params = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        try:
            # Call Operation
            # We import here to avoid potential circular imports if Ops import Models that import Blueprint (unlikely but safe)
            from app.repository.flight.ops.search import SearchFlights
            search_op = SearchFlights()
            results = search_op.execute(params)
            
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
