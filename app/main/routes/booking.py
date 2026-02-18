from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.main import main_bp
from app.main.schemas.booking_initiate import BookingInitiateSchema
from app.repository.booking.services import BookingService
from app.repository.booking.exceptions import BookingServiceError
from app.repository.finance.services import FinanceService
from app.repository.finance.exceptions import FinanceServiceError
from app.utils.upload import UploadService
from app.extensions import db
from marshmallow import ValidationError
import logging
from flask.views import MethodView

# ... imports ...

class PaymentProof(MethodView):
    decorators = [login_required]
    
    def post(self, booking_id):
        # 1. Check if user owns booking
        # We need to get the booking first.
        try:
            booking_service = BookingService(db.session)
            try:
                booking = booking_service.get_booking_by_id(booking_id)
            except Exception: # BookingNotFound alias or generic service error
                 return jsonify({"message": "Booking not found"}), 404
            
            if not booking:
                return jsonify({"message": "Booking not found"}), 404
            
            # Auth check (simplified for now as discussed)
            # Auth check
            if booking.user_id != current_user.id:
                 return jsonify({"message": "Unauthorized"}), 403

            # 2. Handle File Upload
            if 'file' not in request.files:
                return jsonify({"message": "No file part"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"message": "No selected file"}), 400
                
            try:
                receipt_url = UploadService.save_file(file, subdir='receipts')
            except ValueError as e:
                return jsonify({"message": str(e)}), 400
            except IOError:
                return jsonify({"message": "Failed to save file"}), 500

            # 3. Record Payment Proof
            finance_service = FinanceService(db.session)
            payment = finance_service.record_payment_proof(booking_id, receipt_url)
            
            return jsonify({
                "message": "Payment proof uploaded successfully",
                "payment_status": payment.status.value,
                "booking_status": booking.status.value,
                "receipt_url": receipt_url
            }), 201

        except FinanceServiceError as e:
            return jsonify({"message": str(e)}), 400
        except Exception as e:
            logger.error(f"Error uploading proof: {e}", exc_info=True)
            return jsonify({"message": "An unexpected error occurred"}), 500

logger = logging.getLogger(__name__)

class InitiateBooking(MethodView):
    decorators = [login_required]
    
    def post(self):
        # schema validation
        schema = BookingInitiateSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        try:
            service = BookingService(db.session)
            user_id = current_user.id
            
            booking = service.initiate_booking(
                user_id=user_id,
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
main_bp.add_url_rule('/api/booking/<booking_id>/payment-proof', view_func=PaymentProof.as_view('payment_proof'))
