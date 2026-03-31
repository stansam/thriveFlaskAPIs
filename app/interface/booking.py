# services/booking_service.py
"""
BookingService — core transactional service for all booking types.

Implements interfaces.md § 7. BookingService.

Reference number format: TG-YYYY-NNNNNN (thread-safe, DB-unique guaranteed
via retry loop).

Transaction pattern per create*:
  1. Generate reference number
  2. Resolve + snapshot service fee
  3. Create Booking parent row
  4. Create service-type child row (FlightBooking etc.)
  5. Create BookingPassenger rows
  6. If corporate client → CorporateService.increment_booking_usage
  7. Write AuditLog
  8. db.session.commit()
  9. Publish BookingCreatedEvent
"""

from __future__ import annotations

import threading
from datetime import date, datetime, timezone
from decimal import Decimal

from app.models.base import db
from app.models import (
    Booking, FlightBooking, HotelBooking, CarBooking, PackageBooking,
    FlightSegment, BookingPassenger,
)
from app.enums import (
    PackageStatus, FeeType, BookingChannel, AuditActionType,
    BookingStatus, BookingServiceType
)
from app.core.errors.handlers import (
    BadRequestError,
    BusinessRuleViolationError,
    InvalidStatusTransitionError,
    NotFoundError,
)
from app.core.events import event_bus
from app.core.events.dataclasses import (
    BookingCreatedEvent,
    BookingConfirmedEvent,
    BookingCancelledEvent,
    BookingCompletedEvent,
    BookingStatusChangedEvent,
)
from app.core.logging import get_logger
from app.dto import (
    BookingPassengerCreateRequest,
    BookingPassengerResponse,
    BookingStatusTransitionRequest,
    BookingSummaryResponse,
    CarBookingCreateRequest,
    CarBookingResponse,
    CarBookingUpdateRequest,
    FlightBookingCreateRequest,
    FlightBookingResponse,
    FlightBookingUpdateRequest,
    FlightSegmentCreateRequest,
    FlightSegmentResponse,
    HotelBookingCreateRequest,
    HotelBookingResponse,
    HotelBookingUpdateRequest,
    PackageBookingCreateRequest,
    PackageBookingResponse,
    PackageBookingUpdateRequest,
    AuditLogResponse,
)
from app.repository import (
    booking_repo,
    flight_booking_repo,
    hotel_booking_repo,
    car_booking_repo,
    package_booking_repo,
    booking_passenger_repo,
    client_repo,
    package_repo,
    package_price_tier_repo,
    fee_repo,
    fee_snapshot_repo,
    audit_repo,
)
from app.interface._base import BaseService

logger = get_logger(__name__)

# Thread lock for reference number generation
_ref_lock = threading.Lock()

# Allowed status transitions (duplicated here for cheap in-service validation)
_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING_PAYMENT:  {BookingStatus.PAYMENT_RECEIVED, BookingStatus.CANCELLED, BookingStatus.ON_HOLD},
    BookingStatus.PAYMENT_RECEIVED: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.REFUNDED},
    BookingStatus.ON_HOLD:          {BookingStatus.PAYMENT_RECEIVED, BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED:        {BookingStatus.COMPLETED, BookingStatus.CANCELLED},
    BookingStatus.COMPLETED:        set(),
    BookingStatus.CANCELLED:        {BookingStatus.REFUNDED},
    BookingStatus.REFUNDED:         set(),
}


class BookingService(BaseService):
    # Reference number
    def generate_reference_number(self) -> str:
        """Generate a unique TG-YYYY-NNNNNN reference. Thread-safe."""
        with _ref_lock:
            year = datetime.now(timezone.utc).year
            from sqlalchemy import func, select
            count_stmt = (
                select(func.count(Booking.id))
                .where(Booking.reference_number.like(f"TG-{year}-%"))
            )
            count = db.session.execute(count_stmt).scalar_one() + 1
            for _ in range(5):   # retry on collision
                ref = f"TG-{year}-{count:06d}"
                if not booking_repo.exists(reference_number=ref):
                    return ref
                count += 1
            raise RuntimeError("Could not generate unique reference number.")
    # Internal helpers
    def _resolve_fee(
        self,
        fee_type: FeeType,
        num_passengers: int,
        is_emergency: bool,
    ) -> tuple[Decimal, str | None]:
        """Return (amount, fee_id) from the active schedule."""
        from services.fee_service import fee_service
        fee = fee_repo.find_active_by_type(fee_type)
        amount = fee_service.resolve_fee(
            fee_type, num_passengers=num_passengers, is_emergency=is_emergency
        )
        return amount, (fee.id if fee else None)

    def _create_passengers(
        self,
        booking_id: str,
        passengers: list[BookingPassengerCreateRequest],
        actor_id: str,
    ) -> None:
        for p in passengers:
            booking_passenger_repo.create(
                actor_id=actor_id,
                booking_id=booking_id,
                **p.model_dump(),
            )

    def _snapshot_booking(self, b: Booking) -> dict:
        return {
            "id": b.id,
            "reference_number": b.reference_number,
            "status": b.status.value,
            "service_type": b.service_type.value,
            "total_service_fee_usd": str(b.total_service_fee_usd),
        }
    # Queries
    def get_booking(self, booking_id: str):
        b = booking_repo.get_or_404(booking_id)
        return _to_response(b)

    def get_booking_by_reference(self, reference_number: str) -> BookingSummaryResponse:
        b = booking_repo.find_by_reference(reference_number.upper())
        if not b:
            raise NotFoundError("Booking", reference_number)
        return _summary(b)

    def list_bookings(
        self,
        client_id: str | None = None,
        service_type: BookingServiceType | None = None,
        status: BookingStatus | None = None,
        is_emergency: bool | None = None,
        is_group: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        result = booking_repo.paginate_bookings(
            client_id=client_id, service_type=service_type,
            status=status, is_emergency=is_emergency, is_group=is_group,
            date_from=date_from, date_to=date_to, search=search,
            page=page, per_page=per_page,
        )
        return {
            "items": [_summary(b) for b in result.items],
            **self._page_meta(result),
        }

    def get_booking_audit_trail(
        self, booking_id: str, page: int = 1, per_page: int = 50
    ) -> dict:
        booking_repo.get_or_404(booking_id)
        result = audit_repo.find_for_entity("booking", booking_id, page=page, per_page=per_page)
        items = [AuditLogResponse.model_validate(a) for a in result.items]
        return {"items": items, **self._page_meta(result)}
    # Flight booking
    def create_flight_booking(
        self, data: FlightBookingCreateRequest, actor_id: str
    ) -> FlightBookingResponse:
        client_repo.get_or_404(data.client_id)
        ref = self.generate_reference_number()

        fee_type = (
            FeeType.INTERNATIONAL_FLIGHT if data.is_international
            else FeeType.DOMESTIC_FLIGHT
        )
        num_pax = data.num_adults + data.num_children
        if data.is_group:
            fee_type = FeeType.GROUP_PER_PAX
            num_pax = max(num_pax, len(data.passengers))

        fee_amount, fee_id = self._resolve_fee(
            fee_type, num_pax, data.is_emergency
        )

        fb = FlightBooking(
            reference_number=ref,
            service_type=BookingServiceType.FLIGHT,
            status=BookingStatus.PENDING_PAYMENT,
            client_id=data.client_id,
            total_service_fee_usd=fee_amount,
            discount_amount_usd=Decimal("0.00"),
            currency="USD",
            is_emergency=data.is_emergency,
            is_group=data.is_group,
            client_notes=data.client_notes,
            origin_iata=data.origin_iata.upper(),
            destination_iata=data.destination_iata.upper(),
            departure_date=data.departure_date,
            return_date=data.return_date,
            is_round_trip=data.is_round_trip,
            is_international=data.is_international,
            cabin_class=data.cabin_class,
            num_adults=data.num_adults,
            num_children=data.num_children,
            num_infants=data.num_infants,
        )
        fb.set_creator(actor_id)
        db.session.add(fb)
        db.session.flush()

        self._create_passengers(fb.id, data.passengers, actor_id)

        for seg in data.segments:
            db.session.add(FlightSegment(
                flight_booking_id=fb.id, **seg.model_dump()
            ))

        _write_fee_snapshot(fb.id, fee_id, fee_amount, num_pax, BookingChannel.WHATSAPP, data.is_emergency, actor_id)
        _maybe_increment_corporate(data.client_id, actor_id)

        self._audit(
            AuditActionType.CREATE, actor_id, "booking", fb.id,
            f"Flight booking {ref} created for client {data.client_id}.",
            after=self._snapshot_booking(fb),
        )
        db.session.commit()

        event_bus.publish(BookingCreatedEvent(
            booking_id=fb.id, reference_number=ref,
            client_id=data.client_id, service_type="flight", actor_id=actor_id,
        ))
        return FlightBookingResponse.model_validate(fb)

    def update_flight_booking(
        self, booking_id: str, data: FlightBookingUpdateRequest, actor_id: str
    ) -> FlightBookingResponse:
        fb = _get_typed(booking_id, FlightBooking)
        updates = data.model_dump(exclude_none=True)
        if updates:
            flight_booking_repo.update(fb, actor_id=actor_id, **updates)
        self._audit(AuditActionType.UPDATE, actor_id, "booking", booking_id,
                    f"Flight booking {fb.reference_number} updated.")
        db.session.commit()
        return FlightBookingResponse.model_validate(fb)
    # Hotel booking
    def create_hotel_booking(
        self, data: HotelBookingCreateRequest, actor_id: str
    ) -> HotelBookingResponse:
        client_repo.get_or_404(data.client_id)
        ref = self.generate_reference_number()
        fee_amount, fee_id = self._resolve_fee(FeeType.HOTEL, 1, data.is_emergency)

        hb = HotelBooking(
            reference_number=ref,
            service_type=BookingServiceType.HOTEL,
            status=BookingStatus.PENDING_PAYMENT,
            client_id=data.client_id,
            total_service_fee_usd=fee_amount,
            discount_amount_usd=Decimal("0.00"),
            currency="USD",
            is_emergency=data.is_emergency,
            is_group=False,
            client_notes=data.client_notes,
            hotel_name=data.hotel_name,
            hotel_address=data.hotel_address,
            hotel_city=data.hotel_city,
            hotel_country=data.hotel_country,
            star_rating=data.star_rating,
            room_type=data.room_type,
            num_rooms=data.num_rooms,
            num_guests=data.num_guests,
            check_in_date=data.check_in_date,
            check_out_date=data.check_out_date,
            special_requests=data.special_requests,
        )
        hb.set_creator(actor_id)
        db.session.add(hb)
        db.session.flush()

        self._create_passengers(hb.id, data.passengers, actor_id)
        _write_fee_snapshot(hb.id, fee_id, fee_amount, 1, BookingChannel.WHATSAPP, data.is_emergency, actor_id)
        _maybe_increment_corporate(data.client_id, actor_id)

        self._audit(AuditActionType.CREATE, actor_id, "booking", hb.id,
                    f"Hotel booking {ref} created.", after=self._snapshot_booking(hb))
        db.session.commit()

        event_bus.publish(BookingCreatedEvent(
            booking_id=hb.id, reference_number=ref,
            client_id=data.client_id, service_type="hotel", actor_id=actor_id,
        ))
        return HotelBookingResponse.model_validate(hb)

    def update_hotel_booking(
        self, booking_id: str, data: HotelBookingUpdateRequest, actor_id: str
    ) -> HotelBookingResponse:
        hb = _get_typed(booking_id, HotelBooking)
        updates = data.model_dump(exclude_none=True)
        if updates:
            hotel_booking_repo.update(hb, actor_id=actor_id, **updates)
        self._audit(AuditActionType.UPDATE, actor_id, "booking", booking_id,
                    f"Hotel booking {hb.reference_number} updated.")
        db.session.commit()
        return HotelBookingResponse.model_validate(hb)
    # Car booking
    def create_car_booking(
        self, data: CarBookingCreateRequest, actor_id: str
    ) -> CarBookingResponse:
        client_repo.get_or_404(data.client_id)
        ref = self.generate_reference_number()
        fee_amount, fee_id = self._resolve_fee(FeeType.CAR_RENTAL, 1, data.is_emergency)

        cb = CarBooking(
            reference_number=ref,
            service_type=BookingServiceType.CAR,
            status=BookingStatus.PENDING_PAYMENT,
            client_id=data.client_id,
            total_service_fee_usd=fee_amount,
            discount_amount_usd=Decimal("0.00"),
            currency="USD",
            is_emergency=data.is_emergency,
            is_group=False,
            client_notes=data.client_notes,
            rental_company=data.rental_company,
            pickup_location=data.pickup_location,
            dropoff_location=data.dropoff_location,
            pickup_datetime=data.pickup_datetime,
            dropoff_datetime=data.dropoff_datetime,
            car_category=data.car_category,
            num_passengers=data.num_passengers,
            driver_age=data.driver_age,
        )
        cb.set_creator(actor_id)
        db.session.add(cb)
        db.session.flush()

        self._create_passengers(cb.id, data.passengers, actor_id)
        _write_fee_snapshot(cb.id, fee_id, fee_amount, 1, BookingChannel.WHATSAPP, data.is_emergency, actor_id)
        _maybe_increment_corporate(data.client_id, actor_id)

        self._audit(AuditActionType.CREATE, actor_id, "booking", cb.id,
                    f"Car booking {ref} created.", after=self._snapshot_booking(cb))
        db.session.commit()

        event_bus.publish(BookingCreatedEvent(
            booking_id=cb.id, reference_number=ref,
            client_id=data.client_id, service_type="car", actor_id=actor_id,
        ))
        return CarBookingResponse.model_validate(cb)

    def update_car_booking(
        self, booking_id: str, data: CarBookingUpdateRequest, actor_id: str
    ) -> CarBookingResponse:
        cb = _get_typed(booking_id, CarBooking)
        updates = data.model_dump(exclude_none=True)
        if updates:
            car_booking_repo.update(cb, actor_id=actor_id, **updates)
        self._audit(AuditActionType.UPDATE, actor_id, "booking", booking_id,
                    f"Car booking {cb.reference_number} updated.")
        db.session.commit()
        return CarBookingResponse.model_validate(cb)
    # Package booking
    def create_package_booking(
        self, data: PackageBookingCreateRequest, actor_id: str
    ) -> PackageBookingResponse:
        client_repo.get_or_404(data.client_id)
        pkg = package_repo.get_or_404(data.package_id)

        if pkg.status != PackageStatus.ACTIVE:
            raise BusinessRuleViolationError(
                f"Package '{pkg.title}' is not available for booking (status: {pkg.status.value})."
            )

        from services.package_service import package_service
        total_cost = package_service.resolve_price_for_booking(
            data.package_id, data.num_participants, data.add_flights
        )

        # Package service fee: $20 flat (same as hotel fee)
        fee_amount, fee_id = self._resolve_fee(FeeType.HOTEL, 1, data.is_emergency)
        ref = self.generate_reference_number()

        tier = package_price_tier_repo.find_matching_tier(data.package_id, data.num_participants)
        price_per = tier.price_usd if tier else total_cost / data.num_participants

        pb = PackageBooking(
            reference_number=ref,
            service_type=BookingServiceType.PACKAGE,
            status=BookingStatus.PENDING_PAYMENT,
            client_id=data.client_id,
            total_service_fee_usd=fee_amount,
            discount_amount_usd=Decimal("0.00"),
            currency="USD",
            is_emergency=data.is_emergency,
            is_group=data.num_participants >= 5,
            client_notes=data.client_notes,
            package_id=data.package_id,
            selected_price_tier_id=data.selected_price_tier_id,
            num_participants=data.num_participants,
            travel_date=data.travel_date,
            return_date=data.return_date,
            add_flights=data.add_flights,
            add_insurance=data.add_insurance,
            price_per_person_usd=price_per,
            total_package_cost_usd=total_cost,
            customisation_notes=data.customisation_notes,
        )
        pb.set_creator(actor_id)
        db.session.add(pb)
        db.session.flush()

        self._create_passengers(pb.id, data.passengers, actor_id)
        _write_fee_snapshot(pb.id, fee_id, fee_amount, data.num_participants,
                            BookingChannel.WHATSAPP, data.is_emergency, actor_id)
        _maybe_increment_corporate(data.client_id, actor_id)

        self._audit(AuditActionType.CREATE, actor_id, "booking", pb.id,
                    f"Package booking {ref} created.", after=self._snapshot_booking(pb))
        db.session.commit()

        event_bus.publish(BookingCreatedEvent(
            booking_id=pb.id, reference_number=ref,
            client_id=data.client_id, service_type="package", actor_id=actor_id,
        ))
        return PackageBookingResponse.model_validate(pb)

    def update_package_booking(
        self, booking_id: str, data: PackageBookingUpdateRequest, actor_id: str
    ) -> PackageBookingResponse:
        pb = _get_typed(booking_id, PackageBooking)
        updates = data.model_dump(exclude_none=True)
        if updates:
            package_booking_repo.update(pb, actor_id=actor_id, **updates)
        self._audit(AuditActionType.UPDATE, actor_id, "booking", booking_id,
                    f"Package booking {pb.reference_number} updated.")
        db.session.commit()
        return PackageBookingResponse.model_validate(pb)
    # Status transition
    def transition_status(
        self,
        booking_id: str,
        data: BookingStatusTransitionRequest,
        actor_id: str,
    ) -> BookingSummaryResponse:
        booking = booking_repo.get_or_404(booking_id)
        old_status = booking.status
        new_status = data.new_status

        if new_status not in _TRANSITIONS.get(old_status, set()):
            raise InvalidStatusTransitionError(
                f"Cannot transition from '{old_status.value}' to '{new_status.value}'."
            )

        before = {"status": old_status.value}
        booking_repo.transition_status(booking, new_status, actor_id=actor_id)

        self._audit(
            AuditActionType.STATUS_CHANGE, actor_id, "booking", booking_id,
            description=f"Booking {booking.reference_number}: {old_status.value} → {new_status.value}.",
            before=before,
            after={"status": new_status.value, "reason": data.reason},
        )
        db.session.commit()

        # Publish typed event for the most significant transitions
        if new_status == BookingStatus.CONFIRMED:
            event_bus.publish(BookingConfirmedEvent(
                booking_id=booking_id, reference_number=booking.reference_number,
                client_id=booking.client_id, actor_id=actor_id,
            ))
            # Check referral qualification
            from services.referral_service import referral_service
            referral_service.check_and_qualify(booking_id, actor_id)
        elif new_status == BookingStatus.CANCELLED:
            event_bus.publish(BookingCancelledEvent(
                booking_id=booking_id, reference_number=booking.reference_number,
                client_id=booking.client_id, reason=data.reason or "", actor_id=actor_id,
            ))
        elif new_status == BookingStatus.COMPLETED:
            event_bus.publish(BookingCompletedEvent(
                booking_id=booking_id, reference_number=booking.reference_number,
                client_id=booking.client_id,
            ))
        else:
            event_bus.publish(BookingStatusChangedEvent(
                booking_id=booking_id, reference_number=booking.reference_number,
                client_id=booking.client_id, old_status=old_status.value,
                new_status=new_status.value, actor_id=actor_id, reason=data.reason,
            ))

        return _summary(booking)
    # Discount
    def apply_discount(
        self,
        booking_id: str,
        discount_amount: Decimal,
        reason: str,
        actor_id: str,
    ) -> BookingSummaryResponse:
        booking = booking_repo.get_or_404(booking_id)
        if discount_amount < Decimal("0") or discount_amount > booking.total_service_fee_usd:
            raise BadRequestError("Discount amount must be between 0 and the total fee.")
        before = {"discount_amount_usd": str(booking.discount_amount_usd)}
        booking_repo.update(booking, actor_id=actor_id, discount_amount_usd=discount_amount)
        self._audit(
            AuditActionType.UPDATE, actor_id, "booking", booking_id,
            description=f"Discount ${discount_amount} applied: {reason}.",
            before=before,
            after={"discount_amount_usd": str(discount_amount)},
        )
        db.session.commit()
        return _summary(booking)
    # Flight segments
    def add_flight_segment(
        self, booking_id: str, data: FlightSegmentCreateRequest, actor_id: str
    ) -> FlightSegmentResponse:
        fb = _get_typed(booking_id, FlightBooking)
        seg = FlightSegment(flight_booking_id=fb.id, **data.model_dump())
        seg.set_creator(actor_id)
        db.session.add(seg)
        db.session.flush()
        db.session.commit()
        return FlightSegmentResponse.model_validate(seg)

    def update_flight_segment(
        self, segment_id: str, data: dict, actor_id: str
    ) -> FlightSegmentResponse:
        from repositories.booking_repository import BookingPassengerRepository
        from models.booking import FlightSegment as FS
        from sqlalchemy import select
        seg = db.session.get(FS, segment_id)
        if not seg:
            raise NotFoundError("FlightSegment", segment_id)
        for k, v in data.items():
            if v is not None:
                setattr(seg, k, v)
        seg.touch(actor_id)
        db.session.flush()
        db.session.commit()
        return FlightSegmentResponse.model_validate(seg)

    def delete_flight_segment(self, segment_id: str, actor_id: str) -> None:
        from models.booking import FlightSegment as FS
        seg = db.session.get(FS, segment_id)
        if not seg:
            raise NotFoundError("FlightSegment", segment_id)
        db.session.delete(seg)
        db.session.commit()
    # Passengers
    def add_passenger(
        self, booking_id: str, data: BookingPassengerCreateRequest, actor_id: str
    ) -> BookingPassengerResponse:
        booking_repo.get_or_404(booking_id)
        p = booking_passenger_repo.create(actor_id=actor_id, booking_id=booking_id, **data.model_dump())
        db.session.commit()
        return BookingPassengerResponse.model_validate(p)

    def update_passenger(
        self, passenger_id: str, data: dict, actor_id: str
    ) -> BookingPassengerResponse:
        p = booking_passenger_repo.get_or_404(passenger_id)
        booking_passenger_repo.update(p, actor_id=actor_id, **{k: v for k, v in data.items() if v is not None})
        db.session.commit()
        return BookingPassengerResponse.model_validate(p)

    def remove_passenger(self, passenger_id: str, actor_id: str) -> None:
        p = booking_passenger_repo.get_or_404(passenger_id)
        if p.is_lead_passenger:
            others = booking_passenger_repo.find_by_booking(p.booking_id)
            if len(others) > 1:
                raise BadRequestError(
                    "Cannot remove lead passenger when other passengers remain. "
                    "Reassign lead first."
                )
        booking_passenger_repo.delete(p)
        db.session.commit()
# Module-level helper
def _get_typed(booking_id: str, expected_type: type):
    b = booking_repo.get_or_404(booking_id)
    if not isinstance(b, expected_type):
        raise BadRequestError(
            f"Booking {booking_id} is not a {expected_type.__name__}."
        )
    return b


def _write_fee_snapshot(
    booking_id: str, fee_id: str | None, amount: Decimal,
    num_pax: int, channel: BookingChannel, emergency: bool, actor_id: str
) -> None:
    from services.fee_service import fee_service
    fee_service.create_snapshot(
        booking_id=booking_id, fee_id=fee_id,
        applied_amount=amount, num_passengers=num_pax,
        channel=channel, emergency=emergency, actor_id=actor_id,
    )


def _maybe_increment_corporate(client_id: str, actor_id: str) -> None:
    client = client_repo.get(client_id)
    if client and client.corporate_account_id:
        from services.corporate_service import corporate_service
        corporate_service.increment_booking_usage(client.corporate_account_id, actor_id)


def _to_response(b: Booking):
    if isinstance(b, FlightBooking):
        return FlightBookingResponse.model_validate(b)
    if isinstance(b, HotelBooking):
        return HotelBookingResponse.model_validate(b)
    if isinstance(b, CarBooking):
        return CarBookingResponse.model_validate(b)
    if isinstance(b, PackageBooking):
        return PackageBookingResponse.model_validate(b)
    return _summary(b)


def _summary(b: Booking) -> BookingSummaryResponse:
    line = ""
    if isinstance(b, FlightBooking):
        line = f"{b.origin_iata}→{b.destination_iata} {b.departure_date}"
    elif isinstance(b, HotelBooking):
        line = f"{b.hotel_name} {b.check_in_date}"
    elif isinstance(b, CarBooking):
        line = f"{b.pickup_location} {b.pickup_datetime.date()}"
    elif isinstance(b, PackageBooking):
        line = f"Package {b.package_id[:8]}… {b.travel_date}"

    return BookingSummaryResponse(
        id=b.id,
        reference_number=b.reference_number,
        service_type=b.service_type,
        status=b.status,
        client_id=b.client_id,
        is_emergency=b.is_emergency,
        is_group=b.is_group,
        total_service_fee_usd=b.total_service_fee_usd,
        discount_amount_usd=b.discount_amount_usd,
        created_at=b.created_at,
        confirmed_at=b.confirmed_at,
        summary_line=line,
    )


booking_service = BookingService()