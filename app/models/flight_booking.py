from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Integer,
    SmallInteger, String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import BookingServiceType, FlightCabin
from app.models.booking import Booking


class FlightBooking(Booking):
    __tablename__ = "flight_bookings"
    __mapper_args__ = {"polymorphic_identity": BookingServiceType.FLIGHT}

    id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Itinerary summary
    origin_iata: Mapped[str] = mapped_column(
        String(3), nullable=False,
        doc="Departure airport IATA code.",
    )
    destination_iata: Mapped[str] = mapped_column(
        String(3), nullable=False,
        doc="Final destination IATA code.",
    )
    departure_date: Mapped[Date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Date | None] = mapped_column(
        Date, nullable=True,
        doc="NULL for one-way flights.",
    )
    is_round_trip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cabin_class: Mapped[FlightCabin] = mapped_column(
        Enum(FlightCabin, name="flight_cabin_enum"),
        nullable=False,
        default=FlightCabin.ECONOMY,
    )
    num_adults: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    num_children: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    num_infants: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    # Airline confirmation
    pnr: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        doc="Passenger Name Record / airline confirmation code.",
    )
    airline_booking_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True,
        doc="Kayak API deeplink to complete the purchase.",
    )
    ticket_issued_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Domestic / international (drives fee schedule lookup)
    is_international: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Segments
    segments: Mapped[list["FlightSegment"]] = relationship(
        "FlightSegment",
        back_populates="flight_booking",
        cascade="all, delete-orphan",
        order_by="FlightSegment.segment_order",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<FlightBooking {self.reference_number} "
            f"{self.origin_iata}→{self.destination_iata}>"
        )

class FlightSegment(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    """
    One leg of a multi-segment itinerary.

    Example — JFK → DXB with connection via LHR:
      segment_order=1: JFK → LHR, BA178, departs 2024-06-01 09:00
      segment_order=2: LHR → DXB, EK003, departs 2024-06-01 14:30

    `duration_minutes` is stored for display without re-computing from
    departure / arrival timestamps.
    """

    __tablename__ = "flight_segments"

    flight_booking_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("flight_bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, doc="1-indexed leg order."
    )
    origin_iata: Mapped[str] = mapped_column(String(3), nullable=False)
    destination_iata: Mapped[str] = mapped_column(String(3), nullable=False)
    airline_code: Mapped[str | None] = mapped_column(
        String(3), nullable=True, doc="2-letter IATA airline code."
    )
    flight_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    departure_datetime: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    arrival_datetime: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aircraft_type: Mapped[str | None] = mapped_column(String(10), nullable=True)

    flight_booking: Mapped["FlightBooking"] = relationship(
        "FlightBooking", back_populates="segments"
    )

    def __repr__(self) -> str:
        return (
            f"<FlightSegment #{self.segment_order} "
            f"{self.origin_iata}→{self.destination_iata}>"
        )
