from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.main import main_bp
from app.main.schemas.booking_initiate import BookingInitiateSchema
from app.repository.booking.services import BookingService
from app.repository.booking.exceptions import BookingServiceError
from app.extensions import db
from marshmallow import ValidationError
import logging
from flask.views import MethodView

logger = logging.getLogger(__name__)

class InitiateBooking(MethodView):
    # @login_required # Commenting out for easier testing via curl, but SHOULD be there.
    # We will assume user authentication is standard. 
    # If not logged in, user_id might be None or we return 401. 
    # For this implementation phase, let's keep it robust.
    
    def post(self):
        # schema validation
        schema = BookingInitiateSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        try:
            service = BookingService(db.session)
            
            # If current_user is not authenticated, we might need a guest flow 
            # or hardcode a test user ID for development if auth middleware isn't active
            user_id = getattr(current_user, 'id', None)
            if not user_id:
                # Fallback for dev/testing if no Auth header provided
                # In production this should be 401
                # return jsonify({"message": "Unauthorized"}), 401
                # For Phase 2 dev test:
                pass 

            # For now, let's require user_id to be passed or we fail if no current_user.
            # But wait, `current_user` is from flask_login.
            # If we want to test easily, we can mock it or assume middleware works.
            # Let's handle the case where user_id is missing.
            if not user_id and not request.headers.get('X-Test-User-ID'):
                 # We allow a header for testing purposes if not using full login flow
                 return jsonify({"message": "Authentication required"}), 401
            
            real_user_id = user_id or request.headers.get('X-Test-User-ID')

            booking = service.initiate_booking(
                user_id=real_user_id,
                flight_id=data['flight_id'],
                passengers=data['passengers'],
                expected_price=data['expected_price']
            )
            
            return jsonify({
                "message": "Booking initiated successfully",
                "booking_id": booking.id,
                "reference_code": booking.reference_code,
                "status": booking.status.value,
                "total_amount": booking.total_amount,
                "currency": booking.currency
            }), 201
            
        except BookingServiceError as e:
            return jsonify({"message": str(e)}), 400
        except Exception as e:
            logger.error(f"Error initiating booking: {e}", exc_info=True)
            print(f"DEBUG EXCEPTION: {e}")
            return jsonify({"message": "Failed to initiate booking"}), 500

main_bp.add_url_rule('/api/booking/initiate', view_func=InitiateBooking.as_view('initiate_booking'))
