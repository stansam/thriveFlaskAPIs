from sqlalchemy import (
     DateTime, Enum, ForeignKey,
    SmallInteger, String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import BookingServiceType, CarCategory
from .booking import Booking

class CarBooking(Booking):
    """
    Car rental booking.  Service fee: $15 flat.
    """

    __tablename__ = "car_bookings"
    __mapper_args__ = {"polymorphic_identity": BookingServiceType.CAR}

    id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )

    rental_company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    pickup_location: Mapped[str] = mapped_column(String(300), nullable=False)
    dropoff_location: Mapped[str | None] = mapped_column(
        String(300), nullable=True,
        doc="NULL if same as pickup.",
    )
    pickup_datetime: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    dropoff_datetime: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    car_category: Mapped[CarCategory] = mapped_column(
        Enum(CarCategory, name="car_category_enum"),
        nullable=False,
        default=CarCategory.ECONOMY,
    )
    num_passengers: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    confirmation_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    driver_age: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True,
        doc="Driver age; affects rental eligibility and young-driver surcharges.",
    )

    def __repr__(self) -> str:
        return f"<CarBooking {self.reference_number} {self.pickup_location}>"
