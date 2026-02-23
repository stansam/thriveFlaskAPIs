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

class FlightBook(MethodView):
    def post(self):
        try:
            from app.extensions import db
            from app.repository.flight.services import FlightService
            from flask_login import current_user
            
            # Require authentication
            if not getattr(current_user, 'is_authenticated', False):
                return jsonify({"message": "Unauthorized"}), 401
                
            data = request.json
            flight_data = data.get('flight_data')
            amount = data.get('amount')
            currency = data.get('currency', 'USD')
            
            if not flight_data or amount is None:
                return jsonify({"message": "flight_data and amount(base) are required"}), 400
                
            from app.repository.finance.services import FinanceService
            finance_service = FinanceService(db.session)
            
            # calculate fees
            fees = finance_service.calculate_fees("service_fee", amount)
            total_fee_amount = sum(f['amount'] for f in fees)
            total_amount = amount + total_fee_amount
            
            service = FlightService(db.session)
            # using current_user.id assuming it's available. If not, maybe use a dummy for testing.
            user_id = getattr(current_user, 'id', 'test-user-id')
            booking = service.create_manual_booking(user_id, flight_data, total_amount, currency)
            
            return jsonify({"message": "Booking created, payment pending", "booking_id": booking.id, "reference_code": booking.reference_code}), 201
            
        except Exception as e:
            logger.error(f"Error booking flight: {e}")
            return jsonify({"message": "Failed to create booking"}), 500

main_bp.add_url_rule('/api/flight/search', view_func=FlightSearch.as_view('flight_search'))
main_bp.add_url_rule('/api/flight/details/<flight_id>', view_func=FlightDetails.as_view('flight_details'))
main_bp.add_url_rule('/api/flight/book', view_func=FlightBook.as_view('flight_book'))
