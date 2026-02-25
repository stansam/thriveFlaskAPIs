import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.admin.routes.dashboard import admin_required
from app.admin.schemas.bookings import TicketUploadSchema, VoidBookingSchema
from app.services.flight.service import FlightService
from app.models.enums import AuditAction, EntityType
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.utils.upload import UploadService
from flask_login import current_user
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO

logger = logging.getLogger(__name__)

class UploadTicketView(MethodView):
    decorators = [admin_required]

    def post(self, booking_id):
        schema = TicketUploadSchema()
        try:
             data = schema.load(request.form.to_dict())
        except ValidationError as err:
             return jsonify(err.messages), 400

        if 'file' not in request.files or request.files['file'].filename == '':
            return jsonify({"error": "Strictly requires PDF Ticket payload mapping."}), 400
            
        file = request.files['file']
        
        try:
            ticket_url = UploadService.save_file(file, subdir='tickets')
            
            flight_service = FlightService()
            booking = flight_service.flight_booking_repo.update_eticket_info(
                booking_id=booking_id,
                eticket_number=data['eticket_number'],
                ticket_url=ticket_url
            )
            
            log_audit(
                 action=AuditAction.UPDATE,
                 entity_type=EntityType.BOOKING,
                 entity_id=booking_id,
                 user_id=current_user.id,
                 description=f"Generated and attached eTicket {data['eticket_number']} explicitly."
            )
            track_metric("eticket_issued", category="admin")
            
            try:
                ns = NotificationService()
                ns.dispatch_notification(DispatchNotificationDTO(
                     user_id=booking.user_id,
                     trigger_event="ETICKET_ISSUED",
                     context={"ticket_url": ticket_url, "eticket": data['eticket_number']}
                ))
            except Exception as ne:
                logger.error(f"Failing issuing eTicket downstream payload mappings: {ne}")
                
            return jsonify({
                "message": "Ticket legally issued mappings attached.",
                "booking": booking.to_dict()
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400

class VoidBookingView(MethodView):
    decorators = [admin_required]

    def post(self, booking_id):
        schema = VoidBookingSchema()
        try:
             data = schema.load(request.json)
        except ValidationError as err:
             return jsonify(err.messages), 400

        from app.repository import repositories
        booking = repositories.booking.find_by_id(booking_id)
        if not booking:
             return jsonify({"error": "Booking completely unseen within bound graphs."}), 404

        try:
             # Physical Booking cancellation sequence unlocking map boundaries natively
             flight_service = FlightService()
             flight_service.void_booking(booking_id, data['reason'])
             
             log_audit(
                 action=AuditAction.DELETE,
                 entity_type=EntityType.BOOKING,
                 entity_id=booking_id,
                 user_id=current_user.id,
                 description=f"Force-cancelled booking mapping natively. Reason: {data['reason']}"
             )
             track_metric("booking_voided", category="admin")
             
             try:
                ns = NotificationService()
                ns.dispatch_notification(DispatchNotificationDTO(
                     user_id=booking.user_id,
                     trigger_event="BOOKING_CANCELLED",
                     context={"reason": data['reason']}
                ))
             except Exception as ne:
                logger.error(f"Void mapping trigger downstream faulted: {ne}")
                
             return jsonify({"message": "Booking eradicated correctly."}), 200
        except Exception as e:
             return jsonify({"error": str(e)}), 400
