from typing import TYPE_CHECKING
from sqlalchemy import (
    Boolean, ForeignKey, SmallInteger, String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, db

if TYPE_CHECKING:
    from .package import TravelPackage
    from .package_itinerary_days import PackageItineraryDay
    from .media_asset import MediaAsset

class PackageMedia(db.Model, AuditMixin):
    """
    Ordered association between a TravelPackage and its media assets.

    One package has:
      - Exactly one cover image (is_cover=True, display_order=0)
      - 0-N gallery images (is_cover=False, ordered by display_order)
      - 0-N day images linked via itinerary_day_id

    Separating cover from gallery via `is_cover` allows the front-end
    to fetch them independently without filtering on display_order.

    `itinerary_day_id` links a media asset specifically to a day within
    the package itinerary (e.g. Day 2 hero shot of the Desert Safari).
    When NULL the asset belongs to the package-level gallery.
    """

    __tablename__ = "package_media"

    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("travel_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    itinerary_day_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("package_itinerary_days.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Non-null when this image belongs to a specific itinerary day.",
    )
    is_cover: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="True for the single hero/cover image of the package.",
    )
    display_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0,
        doc="Sort order within the gallery or within a day's media.",
    )
    caption: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        doc="Image caption shown beneath the asset in the gallery.",
    )

    # Relationships
    package: Mapped["TravelPackage"] = relationship(
        "TravelPackage", back_populates="media",
    )
    asset: Mapped["MediaAsset"] = relationship(
        "MediaAsset", back_populates="package_media",
    )
    itinerary_day: Mapped["PackageItineraryDay | None"] = relationship(
        "PackageItineraryDay", back_populates="media",
    )

    def __repr__(self) -> str:
        return (
            f"<PackageMedia pkg={self.package_id} "
            f"asset={self.asset_id} cover={self.is_cover}>"
        )
