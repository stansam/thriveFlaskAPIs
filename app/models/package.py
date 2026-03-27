# models/package.py
"""
Travel & Tours Package models.

Domain objects
--------------
TravelPackage          — the catalogue entry (e.g. "Dubai Luxury Escape")
PackagePriceTier       — price variants (solo / couple / group / add-flight)
PackageHighlight       — bullet-point highlights shown on the listing card
PackageInclusion       — included / excluded items (hotel, flights, insurance…)
PackageItineraryDay    — day-by-day programme (Day 1: Desert Safari + BBQ…)

Design decisions
----------------
1.  `TravelPackage` is the aggregate root.  All child tables are hard-deleted
    when the parent is deleted (CASCADE).

2.  Pricing is normalised into `PackagePriceTier` so the same package can
    offer e.g. "from $1,899 solo" and "from $1,599 pp for group of 6+".

3.  `PackageInclusion` uses an `InclusionType` enum (INCLUDED / EXCLUDED /
    OPTIONAL) matching the ✔ / ✘ / ✨ business language in the business plan.

4.  `PackageItineraryDay` stores one row per day, supporting rich per-day
    descriptions, activity lists, and optional meal flags.

5.  `display_order` columns on child tables control front-end sort order
    without requiring re-inserts.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Enum, Numeric, SmallInteger, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, db
from app.enums import PackageStatus

if TYPE_CHECKING:
    from .booking import PackageBooking
    from .package_media import PackageMedia

class TravelPackage(db.Model, AuditMixin):
    """
    Master catalogue entry for a travel package.

    Example: Dubai Luxury Escape — 5 Days / 4 Nights, from $1,899 pp.

    `slug` is a URL-safe identifier generated from the title, used in
    marketing URLs.  It must be unique across active packages.

    `destination_country` / `destination_city` support future filtering
    (e.g. "Show me all packages in Europe").

    `min_participants` / `max_participants` gate group-size validation
    at booking time.

    `flights_includable` flags whether the "Flights can be added"
    option exists, triggering a FlightBooking to be attached.
    """

    __tablename__ = "travel_packages"

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
    bookings: Mapped[list["PackageBooking"]] = relationship(
        "PackageBooking",
        back_populates="package",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<TravelPackage {self.title!r} [{self.status.value}]>"
