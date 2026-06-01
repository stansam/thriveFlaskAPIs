# services/media_service.py
"""
MediaService — file upload and management.

Implements interfaces.md § 6. MediaService.
"""

from __future__ import annotations

import hashlib
import io
import os
import uuid
from pathlib import Path

from app.models.base import db
from app.enums import AuditActionType, AssetType, AssetOwnerType, StorageBackend
from app.core.config import settings
from app.core.errors.handlers import BadRequestError, ConflictError, BusinessRuleViolationError
from app.core.logging import get_logger
from app.dto import (
    MediaAssetResponse,
    MediaAssetUploadRequest,
    PackageMediaResponse,
)
from app.repository import media_repo, package_media_repo
from app.interface._base import BaseService

logger = get_logger(__name__)

_IMAGE_TYPES = {AssetType.IMAGE_JPEG, AssetType.IMAGE_PNG, AssetType.IMAGE_WEBP, AssetType.IMAGE_GIF}
_MAX_BYTES = settings.STORAGE_MAX_FILE_SIZE_MB * 1024 * 1024


class MediaService(BaseService):

    def upload_asset(self, file, metadata: MediaAssetUploadRequest, actor_id: str) -> MediaAssetResponse:
        data = file.read() if hasattr(file, "read") else file
        if len(data) > _MAX_BYTES:
            raise BadRequestError(f"File exceeds maximum size of {settings.STORAGE_MAX_FILE_SIZE_MB} MB.")

        checksum = hashlib.sha256(data).hexdigest()
        existing = media_repo.find_by_checksum(checksum)
        if existing:
            raise ConflictError(f"An identical file already exists (id={existing.id}).")

        filename = getattr(file, "filename", "upload") or "upload"
        ext = Path(filename).suffix.lower()
        storage_key = f"{uuid.uuid4().hex}{ext}"
        cdn_url = self._store(data, storage_key)

        width_px, height_px = None, None
        if metadata.asset_type in _IMAGE_TYPES:
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(data))
                width_px, height_px = img.size
            except Exception:
                pass

        asset = media_repo.create(
            actor_id=actor_id,
            original_filename=filename,
            storage_key=storage_key,
            storage_backend=StorageBackend(settings.STORAGE_BACKEND),
            cdn_url=cdn_url,
            asset_type=metadata.asset_type,
            file_size_bytes=len(data),
            width_px=width_px,
            height_px=height_px,
            alt_text=metadata.alt_text,
            is_public=metadata.is_public,
            owner_type=metadata.owner_type,
            owner_id=metadata.owner_id,
            checksum_sha256=checksum,
        )
        self._audit(AuditActionType.CREATE, actor_id, "media_asset", asset.id,
                    description=f"Asset '{filename}' uploaded ({metadata.asset_type.value}).")
        db.session.commit()
        return MediaAssetResponse.model_validate(asset)

    def get_asset(self, asset_id: str) -> MediaAssetResponse:
        asset = media_repo.get_or_404(asset_id)
        return MediaAssetResponse.model_validate(asset)

    def delete_asset(self, asset_id: str, actor_id: str) -> None:
        asset = media_repo.get_or_404(asset_id)
        covers = package_media_repo.list_by(asset_id=asset_id, is_cover=True)
        if covers:
            raise BusinessRuleViolationError("Cannot delete an asset used as a package cover.")
        self._delete_from_storage(asset.storage_key)
        media_repo.delete(asset)
        self._audit(AuditActionType.DELETE, actor_id, "media_asset", asset_id,
                    description=f"Asset '{asset.original_filename}' deleted.")
        db.session.commit()

    def attach_to_package(
        self, package_id: str, asset_id: str, is_cover: bool,
        display_order: int, caption: str | None, actor_id: str
    ) -> PackageMediaResponse:
        if is_cover:
            pm = package_media_repo.set_cover(package_id, asset_id, actor_id=actor_id)
        else:
            pm = package_media_repo.create(
                actor_id=actor_id, package_id=package_id,
                asset_id=asset_id, is_cover=False,
                display_order=display_order, caption=caption,
            )
        db.session.commit()
        return PackageMediaResponse.model_validate(pm)

    def attach_to_day(
        self, itinerary_day_id: str, asset_id: str,
        display_order: int, caption: str | None, actor_id: str
    ) -> PackageMediaResponse:
        from app.models.package import PackageItineraryDay
        day = db.session.get(PackageItineraryDay, itinerary_day_id)
        if not day:
            from app.core.errors.handlers import NotFoundError
            raise NotFoundError("PackageItineraryDay", itinerary_day_id)
        pm = package_media_repo.create(
            actor_id=actor_id, package_id=day.package_id,
            asset_id=asset_id, itinerary_day_id=itinerary_day_id,
            is_cover=False, display_order=display_order, caption=caption,
        )
        db.session.commit()
        return PackageMediaResponse.model_validate(pm)

    def detach_from_package(self, package_media_id: str, actor_id: str) -> None:
        pm = package_media_repo.get_or_404(package_media_id)
        package_media_repo.delete(pm)
        db.session.commit()

    def set_package_cover(
        self, package_id: str, asset_id: str, actor_id: str
    ) -> PackageMediaResponse:
        pm = package_media_repo.set_cover(package_id, asset_id, actor_id=actor_id)
        db.session.commit()
        return PackageMediaResponse.model_validate(pm)

    def reorder_gallery(
        self, package_id: str, ordered_asset_ids: list[str], actor_id: str
    ) -> None:
        gallery = package_media_repo.find_gallery(package_id)
        asset_to_pm = {pm.asset_id: pm for pm in gallery}
        for idx, asset_id in enumerate(ordered_asset_ids):
            if asset_id in asset_to_pm:
                package_media_repo.update(asset_to_pm[asset_id], actor_id=actor_id, display_order=idx)
        db.session.commit()

    def generate_signed_url(self, asset_id: str, expires_in_seconds: int = 3600) -> str:
        asset = media_repo.get_or_404(asset_id)
        if settings.STORAGE_BACKEND == "s3":
            return self._s3_signed_url(asset.storage_key, expires_in_seconds)
        return asset.cdn_url   # local: return direct URL

    # ------------------------------------------------------------------
    # Storage backend dispatch
    # ------------------------------------------------------------------

    def _store(self, data: bytes, key: str) -> str:
        if settings.STORAGE_BACKEND == "local":
            return self._store_local(data, key)
        elif settings.STORAGE_BACKEND == "s3":
            return self._store_s3(data, key)
        return self._store_local(data, key)

    def _store_local(self, data: bytes, key: str) -> str:
        upload_dir = Path(settings.STORAGE_LOCAL_UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        (upload_dir / key).write_bytes(data)
        return f"{settings.CDN_BASE_URL}/{key}"

    def _store_s3(self, data: bytes, key: str) -> str:
        import boto3
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
        )
        s3.put_object(Bucket=settings.AWS_S3_BUCKET, Key=key, Body=data)
        return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"

    def _delete_from_storage(self, key: str) -> None:
        if settings.STORAGE_BACKEND == "local":
            try:
                (Path(settings.STORAGE_LOCAL_UPLOAD_DIR) / key).unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("Local file delete failed for key %s: %s", key, exc)
        elif settings.STORAGE_BACKEND == "s3":
            try:
                import boto3
                boto3.client("s3").delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
            except Exception as exc:
                logger.warning("S3 delete failed for key %s: %s", key, exc)

    def _s3_signed_url(self, key: str, expires: int) -> str:
        import boto3
        s3 = boto3.client("s3")
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
            ExpiresIn=expires,
        )


media_service = MediaService()