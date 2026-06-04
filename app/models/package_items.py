from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Enum, ForeignKey, Numeric, SmallInteger, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import InclusionType

if TYPE_CHECKING:
    from app.models.package import TravelPackage
    from app.models.package_media import PackageMedia

# PackageHighlight
class PackageHighlight(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "package_highlights"

    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("travel_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    icon: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        doc="Optional emoji or icon key for the front-end (e.g. '🏨', 'hotel').",
    )
    display_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0
    )

    package: Mapped["TravelPackage"] = relationship(
        "TravelPackage", back_populates="highlights"
    )

    def __init__(self, **kwargs: Any) -> None:
        super(PackageHighlight, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<PackageHighlight {self.text[:40]!r}>"

# PackageInclusion
class PackageInclusion(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    """
    One ✔ / ✘ / + line in the What's Included / Excluded section.

    Example rows:
      INCLUDED  — "Hotel"
      INCLUDED  — "Breakfast daily"
      EXCLUDED  — "Flights (can be added)"
      EXCLUDED  — "Travel insurance"
      OPTIONAL  — "Single room supplement (+$200)"
    """

    __tablename__ = "package_inclusions"

    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("travel_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inclusion_type: Mapped[InclusionType] = mapped_column(
        Enum(InclusionType, name="inclusion_type_enum"),
        nullable=False,
        doc="INCLUDED / EXCLUDED / OPTIONAL",
    )
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    notes: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        doc="Clarifying note shown in parentheses, e.g. 'can be added'.",
    )
    extra_cost_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True,
        doc="Populated for OPTIONAL items that carry an additional fee.",
    )
    display_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    package: Mapped["TravelPackage"] = relationship(
        "TravelPackage", back_populates="inclusions"
    )

    def __init__(self, **kwargs: Any) -> None:
        super(PackageInclusion, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<PackageInclusion [{self.inclusion_type.value}] {self.label!r}>"

# PackageItineraryDay
class PackageItineraryDay(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    """
    One day in the package itinerary.

    Example (Dubai, Day 1):
      day_number  = 1
      title       = "Arrival & Dubai Marina"
      description = "Check in to 4-star hotel. Evening yacht cruise on the Marina."
      activities  = "Airport transfer, hotel check-in, Dubai Marina Yacht Cruise"
      meals_included = "Dinner"
      accommodation  = "Rove Downtown Dubai"

    `activities` is stored as free text (newline-separated bullet points) for
    simplicity.  A future v2 could normalise into a PackageActivity table if
    richer querying is needed.
    """

    __tablename__ = "package_itinerary_days"

    __table_args__ = (
        UniqueConstraint(
            "package_id", "day_number",
            name="uq_package_itinerary_days_package_day"
        ),
    )

    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("travel_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number: Mapped[int] = mapped_column(
        SmallInteger, nullable=False,
        doc="1-indexed day number within the itinerary.",
    )
    title: Mapped[str] = mapped_column(
        String(300), nullable=False,
        doc='Short day title, e.g. "Desert Safari & Abu Dhabi".',
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        doc="Rich narrative for the day (HTML/Markdown).",
    )
    activities: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        doc="Newline-separated activity bullet points.",
    )
    meals_included: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        doc='Comma-separated meals, e.g. "Breakfast, Dinner".',
    )
    accommodation: Mapped[str | None] = mapped_column(
        String(300), nullable=True,
        doc="Hotel / resort name for the night.",
    )
    image_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True,
        doc="CDN URL for the day's hero image.",
    )

    package: Mapped["TravelPackage"] = relationship(
        "TravelPackage", back_populates="itinerary_days"
    )
    media: Mapped[list["PackageMedia"]] = relationship(
        "PackageMedia",
        back_populates="itinerary_day",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __init__(self, **kwargs: Any) -> None:
        super(PackageItineraryDay, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<PackageItineraryDay Day {self.day_number}: {self.title!r}>"