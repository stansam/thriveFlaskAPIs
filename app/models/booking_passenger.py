from sqlalchemy import (
    Boolean, Date, 
    ForeignKey, String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import AuditMixin, db

class BookingPassenger(db.Model, AuditMixin):
    """
    A traveller attached to a booking.

    For solo bookings there is one passenger row matching the client.
    For group bookings each traveller gets their own row.

    `passport_number` is denormalised here (vs Client.passport_number)
    because the client may travel on a different passport next time, and
    we need a point-in-time snapshot for each trip.
    """

    __tablename__ = "booking_passengers"

    booking_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    passport_expiry: Mapped[Date | None] = mapped_column(Date, nullable=True)
    is_lead_passenger: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="The lead traveller / primary contact for this booking.",
    )
    seat_preference: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        doc='e.g. "window", "aisle", "extra legroom".',
    )
    meal_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    special_assistance: Mapped[str | None] = mapped_column(
        String(300), nullable=True,
        doc="Wheelchair, oxygen, dietary, etc.",
    )

    booking: Mapped["Booking"] = relationship("Booking", back_populates="passengers")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<BookingPassenger {self.full_name} [booking={self.booking_id}]>"

