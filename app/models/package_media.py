from typing import TYPE_CHECKING
from sqlalchemy import (
    Boolean, ForeignKey, SmallInteger, String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db

if TYPE_CHECKING:
    from app.models.package import TravelPackage
    from app.models.package_itinerary_days import PackageItineraryDay
    from app.models.media_asset import MediaAsset

class PackageMedia(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
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
