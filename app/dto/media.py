# dtos/media.py
from __future__ import annotations
from typing import Annotated
from pydantic import Field
from app.enums import AssetType, AssetOwnerType, StorageBackend
from .common import AuditFieldsMixin, StrictRequestModel

class MediaAssetUploadRequest(StrictRequestModel):
    asset_type: AssetType
    owner_type: AssetOwnerType | None = None
    owner_id: str | None = None
    alt_text: Annotated[str | None, Field(default=None, max_length=500)] = None
    is_public: bool = True

class MediaAssetResponse(AuditFieldsMixin):
    original_filename: str
    cdn_url: str
    storage_backend: StorageBackend
    asset_type: AssetType
    file_size_bytes: int | None
    width_px: int | None
    height_px: int | None
    alt_text: str | None
    is_public: bool
    owner_type: AssetOwnerType | None
    owner_id: str | None

class PackageMediaResponse(AuditFieldsMixin):
    package_id: str
    asset_id: str
    itinerary_day_id: str | None
    is_cover: bool
    display_order: int
    caption: str | None
    asset: MediaAssetResponse | None = None
