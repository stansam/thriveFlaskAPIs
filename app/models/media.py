# models/media.py
"""
Supported asset types
---------------------
IMAGE_JPEG, IMAGE_PNG, IMAGE_WEBP  — marketing / itinerary images
IMAGE_GIF                          — lightweight animated promos
DOCUMENT_PDF                       — booking confirmations, e-tickets
RECEIPT                            — payment proof uploads (admin)
AVATAR                             — user/client profile photos
"""
from typing import TYPE_CHECKING
from sqlalchemy import (
    BigInteger, Boolean, Enum, Integer, String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import AssetType, AssetOwnerType, StorageBackend

if TYPE_CHECKING:
    from app.models.package_itinerary_days import PackageItineraryDay
    from app.models.package_media import PackageMedia
    

class MediaAsset(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    """
    A single uploaded file, owned by one domain entity.

    Columns
    -------
    original_filename   Name the user uploaded (sanitised before storing).
    storage_key         Path / object key inside the storage backend.
    storage_backend     Which CDN / bucket holds the file.
    cdn_url             Public CDN URL (primary access URL).
    asset_type          MIME-type enum — drives validation and rendering.
    file_size_bytes     Used for storage quota tracking.
    width_px / height_px Populated for image assets after processing.
    alt_text            Accessibility alt text for images.
    is_public           False for receipts / sensitive documents.
    owner_type          Which model owns this asset.
    owner_id            PK of the owning record (polymorphic, not a real FK).
    checksum_sha256     File integrity hash; verified on upload.
    """

    __tablename__ = "media_assets"

    # File identity
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(
        String(1000), nullable=False, unique=True,
        doc="Object key / path inside the storage bucket.",
    )
    storage_backend: Mapped[StorageBackend] = mapped_column(
        Enum(StorageBackend, name="storage_backend_enum"),
        nullable=False,
        default=StorageBackend.LOCAL,
    )
    cdn_url: Mapped[str] = mapped_column(
        String(2048), nullable=False,
        doc="Public URL used in API responses and front-end rendering.",
    )

    # Asset metadata
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type_enum"),
        nullable=False,
        index=True,
    )
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    alt_text: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        doc="Screen-reader accessible description for image assets.",
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="False for receipts and sensitive documents; signed URLs only.",
    )
    checksum_sha256: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
        doc="SHA-256 hex digest verified on upload.",
    )

    # Polymorphic ownership
    owner_type: Mapped[AssetOwnerType | None] = mapped_column(
        Enum(AssetOwnerType, name="asset_owner_type_enum"),
        nullable=True,
        index=True,
        doc="Which model owns this asset.",
    )
    owner_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True,
        doc="PK of the owning model row (not a real DB FK — polymorphic).",
    )

    # Relationships (back-refs from junction tables)
    package_media: Mapped[list["PackageMedia"]] = relationship(
        "PackageMedia",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MediaAsset {self.asset_type.value} {self.original_filename!r}>"


