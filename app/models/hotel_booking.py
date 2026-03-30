from sqlalchemy import Date, Enum, ForeignKey, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.enums import BookingServiceType, RoomType
from app.models.booking import Booking

class HotelBooking(Booking):
    __tablename__ = "hotel_bookings"
    __mapper_args__ = {"polymorphic_identity": BookingServiceType.HOTEL}

    id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        primary_key=True,
    )

    hotel_name: Mapped[str] = mapped_column(String(300), nullable=False)
    hotel_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    hotel_city: Mapped[str] = mapped_column(String(100), nullable=False)
    hotel_country: Mapped[str] = mapped_column(String(100), nullable=False)
    star_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    room_type: Mapped[RoomType] = mapped_column(
        Enum(RoomType, name="room_type_enum"),
        nullable=False,
        default=RoomType.STANDARD,
    )
    num_rooms: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    num_guests: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    check_in_date: Mapped[Date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[Date] = mapped_column(Date, nullable=False)
    confirmation_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        doc="Hotel's own booking confirmation code.",
    )
    special_requests: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<HotelBooking {self.reference_number} {self.hotel_name}>"
