from flask import Blueprint, request, jsonify
from flask.views import MethodView
from app.repository.booking.services import BookingService
from app.repository.finance.services import FinanceService
from app.repository.finance.exceptions import FinanceServiceError
from app.repository.booking.exceptions import BookingServiceError, BookingNotFound
from app.utils.upload import UploadService
from app.extensions import db
import logging

admin_booking_bp = Blueprint('admin_booking', __name__)
logger = logging.getLogger(__name__)

from flask_login import login_required, current_user
from app.models.enums import UserRole

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.ADMIN:
             return jsonify({"message": "Forbidden: Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

class VerifyPaymentView(MethodView):
    decorators = [admin_required]
    
    def post(self, booking_id):
        data = request.json or {}
        status = data.get('status') # 'approved' or 'rejected'
        rejection_reason = data.get('rejection_reason')
        
        if status not in ['approved', 'rejected']:
             return jsonify({"message": "Invalid status. Must be 'approved' or 'rejected'"}), 400
             
        verified = (status == 'approved')
        
        try:
            finance_service = FinanceService(db.session)
            payment = finance_service.verify_payment(booking_id, verified, rejection_reason)
            
            return jsonify({
                "message": f"Payment {'verified' if verified else 'rejected'}",
                "payment_status": payment.status.value,
                # "booking_status": payment.booking.status.value # If relation is loaded
            }), 200

        except FinanceServiceError as e:
            return jsonify({"message": str(e)}), 400
        except Exception as e:
            logger.error(f"Error verifying payment: {e}", exc_info=True)
            return jsonify({"message": "An unexpected error occurred"}), 500

class UploadTicketView(MethodView):
    decorators = [admin_required]
    
    def post(self, booking_id):
        if 'file' not in request.files:
            return jsonify({"message": "No file part"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"message": "No selected file"}), 400
            
        try:
            # We use 'tickets' subdirectory
            ticket_url = UploadService.save_file(file, subdir='tickets')
            
            pnr = request.form.get('pnr_reference')
            eticket = request.form.get('eticket_number')
            
            from app.repository.flight.services import FlightService
            flight_service = FlightService(db.session)
            
            if pnr and eticket:
                flight_booking = flight_service.admin_fulfill_ticket(booking_id, pnr, eticket, ticket_url)
                booking_status = flight_booking.booking.status.value if flight_booking.booking else BookingStatus.COMPLETED.value
            else:
                booking_service = BookingService(db.session)
                booking = booking_service.upload_ticket(booking_id, ticket_url)
                booking_status = booking.status.value
            
            return jsonify({
                "message": "Ticket uploaded successfully",
                "booking_status": booking_status,
                "ticket_url": ticket_url
            }), 200
            
        except BookingNotFound as e:
            return jsonify({"message": str(e)}), 404
        except BookingServiceError as e:
            return jsonify({"message": str(e)}), 400
        except ValueError as e: # From UploadService
             return jsonify({"message": str(e)}), 400
        except Exception as e:
            logger.error(f"Error uploading ticket: {e}", exc_info=True)
            return jsonify({"message": "An unexpected error occurred"}), 500

admin_booking_bp.add_url_rule('/booking/<booking_id>/verify', view_func=VerifyPaymentView.as_view('verify_payment'))
admin_booking_bp.add_url_rule('/booking/<booking_id>/ticket', view_func=UploadTicketView.as_view('upload_ticket'))
