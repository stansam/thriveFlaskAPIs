import logging
from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from datetime import datetime

from app.client.schemas.booking import FlightBookingSchema, PackageBookingSchema, BookingPassengersSchema
from app.dto.flight.schemas import BookFlightDTO, FlightSegmentDTO
from app.dto.package.schemas import BookPackageDTO
from app.services.flight.service import FlightService
from app.services.package.service import PackageService
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType

logger = logging.getLogger(__name__)

class UserBookingsView(MethodView):
    decorators = [login_required]

    def get(self):
        """Pulls list of bookings specifically for current active identity."""
        from app.repository import repositories
        bookings = repositories.booking.search_by_factors(user_id=current_user.id)
        
        track_metric(metric_name="user_bookings_viewed", category="client")
        return jsonify([b.to_dict() for b in bookings]), 200


class FlightBookingView(MethodView):
    decorators = [login_required]

    def post(self):
        schema = FlightBookingSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        flight_service = FlightService()
        segments_dto = []
        for seg in data['segments']:
             segments_dto.append(FlightSegmentDTO(
                 carrier_code=seg['carrier_code'],
                 flight_number=seg['flight_number'],
                 departure_airport_code=seg['departure_airport_code'],
                 arrival_airport_code=seg['arrival_airport_code'],
                 departure_time=seg['departure_time'], # Marshmallow outputs Datetime natively
                 arrival_time=seg['arrival_time'],
                 duration_minutes=seg.get('duration_minutes'),
                 aircraft_type=seg.get('aircraft_type'),
                 baggage_allowance=seg.get('baggage_allowance'),
                 terminal=seg.get('terminal'),
                 gate=seg.get('gate')
             ))

        payload = BookFlightDTO(
            user_id=current_user.id,
            cabin_class=data['cabin_class'],
            segments=segments_dto,
            pnr_reference=data.get('pnr_reference')
        )
        
        try:
            booking = flight_service.book_flight(payload)
            track_metric(metric_name="flight_booking_initiated", category="client")
            log_audit(
                action=AuditAction.CREATE,
                entity_type=EntityType.BOOKING,
                entity_id=booking.id,
                user_id=current_user.id,
                description=f"Generated flight booking {booking.reference_code}"
            )
            
            # Fire Async Email Invoice dispatch cleanly
            try:
                ns = NotificationService()
                ns.dispatch_notification(DispatchNotificationDTO(
                    user_id=current_user.id,
                    trigger_event="BOOKING_CREATED",
                    context={"booking": booking.to_dict()}
                ))
            except Exception as e:
                logger.error(f"Failed dispatching flight notification: {e}")
                
            return jsonify({"message": "Flight reserved.", "booking": booking.to_dict()}), 201

        except Exception as e:
             logger.error(f"Flight logic error: {e}")
             return jsonify({"error": str(e)}), 400


class PackageBookingView(MethodView):
    decorators = [login_required]

    def post(self):
        schema = PackageBookingSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        package_service = PackageService()
        payload = BookPackageDTO(
            user_id=current_user.id,
            package_id=data['package_id'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            number_of_adults=data['number_of_adults'],
            number_of_children=data['number_of_children'],
            special_requests=data.get('special_requests')
        )
        
        try:
            booking = package_service.book_package(payload)
            track_metric(metric_name="package_booking_initiated", category="client")
            log_audit(
                action=AuditAction.CREATE,
                entity_type=EntityType.BOOKING,
                entity_id=booking.id,
                user_id=current_user.id,
                description=f"Generated package booking {booking.reference_code}"
            )
            
            try:
                ns = NotificationService()
                ns.dispatch_notification(DispatchNotificationDTO(
                    user_id=current_user.id,
                    trigger_event="BOOKING_CREATED",
                    context={"booking": booking.to_dict()}
                ))
            except Exception as e:
                logger.error(f"Failed dispatching package notification: {e}")
                
            return jsonify({"message": "Package reserved implicitly.", "booking": booking.to_dict()}), 201
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400


class BookingPassengersView(MethodView):
    decorators = [login_required]

    def post(self, booking_id):
        """Append group passenger arrays onto an active PENDING booking natively"""
        schema = BookingPassengersSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        from app.repository import repositories
        booking = repositories.booking.find_by_id(booking_id)
        
        if not booking or booking.user_id != current_user.id:
            return jsonify({"error": "Booking not found or not owned."}), 404

        # In production `FlightService` or `PackageService` binds passengers natively into DB mappings
        from app.models.passenger import Passenger
        from app.extensions import db
        pass_list = []
        for p_data in data['passengers']:
             new_p = Passenger(
                 booking_id=booking.id,
                 first_name=p_data['first_name'],
                 last_name=p_data['last_name'],
                 date_of_birth=p_data['date_of_birth'],
                 passport_number=p_data.get('passport_number')
             )
             db.session.add(new_p)
             pass_list.append(new_p)
             
        db.session.commit()
        track_metric(metric_name="group_passengers_added", category="client", value=len(pass_list))
        log_audit(
            action=AuditAction.UPDATE,
            entity_type=EntityType.BOOKING,
            entity_id=booking.id,
            user_id=current_user.id,
            description=f"Attached {len(pass_list)} passengers to booking."
        )

        return jsonify({"message": "Passengers successfully attached.", "count": len(pass_list)}), 200
