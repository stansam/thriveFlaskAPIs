from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean, Enum, Numeric, SmallInteger, String, Text, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import PackageStatus

if TYPE_CHECKING:
    from app.models.package_booking import PackageBooking
    from app.models.package_media import PackageMedia
    from app.models.package_items import PackageHighlight, PackageInclusion, PackageItineraryDay
    from app.models.package_price_tier import PackagePriceTier
    from app.models.package_insurance import PackageInsurance

class TravelPackage(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "travel_packages"

    __table_args__ = (
        CheckConstraint(
            "duration_days >= duration_nights",
            name="ck_travel_packages_duration_days_gte_nights"
        ),
        CheckConstraint(
            "min_participants >= 1",
            name="ck_travel_packages_min_participants_positive"
        ),
        CheckConstraint(
            "base_price_usd > 0",
            name="ck_travel_packages_base_price_positive"
        ),
    )

    # Identity & copy
    title: Mapped[str] = mapped_column(
        String(300), nullable=False, doc='e.g. "Dubai Luxury Escape"'
    )
    slug: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True,
        doc="URL-safe version of the title.",
    )
    tagline: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        doc='Short marketing line, e.g. "Yacht Cruise • Desert Safari • Burj Khalifa"',
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Full rich-text description (HTML/Markdown)."
    )
    status: Mapped[PackageStatus] = mapped_column(
        Enum(PackageStatus, name="package_status_enum"),
        nullable=False,
        default=PackageStatus.DRAFT,
        index=True,
    )

    # Destination
    destination_country: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        doc='e.g. "Middle East", "Southeast Asia" — for front-end filtering.',
    )

    # Duration
    duration_days: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, doc="Number of days (e.g. 5)."
    )
    duration_nights: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, doc="Number of nights (e.g. 4)."
    )

    # Pricing anchor (lowest advertised price for marketing display)
    base_price_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        doc='The "from $X" price shown on listing cards.',
    )
    price_per: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="person",
        doc='"person", "couple", "group" — qualifies base_price_usd.',
    )

    # Participant constraints
    min_participants: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1
    )
    max_participants: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, doc="NULL = no cap."
    )

    # Flags
    flights_includable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="Whether flights can be added to this package.",
    )
    insurance_includable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="Whether travel insurance can be added.",
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="Pinned to homepage / featured section.",
    )

    # Media
    cover_image_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True, doc="CDN URL for the hero image."
    )
    gallery_urls: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        doc="JSON array of CDN image URLs for the gallery carousel.",
    )

    # Relationships
    highlights: Mapped[list["PackageHighlight"]] = relationship(
        "PackageHighlight",
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="PackageHighlight.display_order",
        lazy="selectin",
    )
    inclusions: Mapped[list["PackageInclusion"]] = relationship(
        "PackageInclusion",
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="PackageInclusion.inclusion_type, PackageInclusion.display_order",
        lazy="selectin",
    )
    itinerary_days: Mapped[list["PackageItineraryDay"]] = relationship(
        "PackageItineraryDay",
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="PackageItineraryDay.day_number",
        lazy="selectin",
    )
    price_tiers: Mapped[list["PackagePriceTier"]] = relationship(
        "PackagePriceTier",
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="PackagePriceTier.min_participants",
        lazy="selectin",
    )
    media: Mapped[list["PackageMedia"]] = relationship(
        "PackageMedia",
        back_populates="package",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    insurance_options: Mapped[list["PackageInsurance"]] = relationship(
        "PackageInsurance",
        back_populates="package",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    bookings: Mapped[list["PackageBooking"]] = relationship(
        "PackageBooking",
        back_populates="package",
        lazy="dynamic",
    )

    def __init__(self, **kwargs: Any) -> None:
        super(TravelPackage, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<TravelPackage {self.title!r} [{self.status.value}]>"
