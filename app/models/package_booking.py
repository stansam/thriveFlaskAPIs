from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Date, ForeignKey, Numeric,
    SmallInteger, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import BookingServiceType

if TYPE_CHECKING:
    from app.models.package import TravelPackage

from .booking import Booking

class PackageBooking(Booking):
    __tablename__ = "package_bookings"
    __mapper_args__ = {"polymorphic_identity": BookingServiceType.PACKAGE}

    id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )

    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("travel_packages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    selected_price_tier_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("package_price_tiers.id", ondelete="SET NULL"),
        nullable=True,
        doc="The tier locked in at booking time.",
    )
    num_participants: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1
    )
    travel_date: Mapped[Date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    add_flights: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="Client opted-in to add flights to the package.",
    )
    add_insurance: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
    )
    linked_flight_booking_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("flight_bookings.id", ondelete="SET NULL"),
        nullable=True,
        doc="Optional companion FlightBooking when add_flights=True.",
    )
    price_per_person_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="Per-person price locked in at booking time.",
    )
    total_package_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
        doc="price_per_person × num_participants (informational).",
    )
    customisation_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        doc="Any bespoke adjustments requested by the client.",
    )

    package: Mapped["TravelPackage"] = relationship(
        "TravelPackage", back_populates="bookings"
    )

    def __repr__(self) -> str:
        return f"<PackageBooking {self.reference_number} pkg={self.package_id}>"
