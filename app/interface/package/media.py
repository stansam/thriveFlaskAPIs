from __future__ import annotations

from typing import Any
import logging

from app.enums import AuditActionType
from app.core.errors.handlers import (
    BusinessRuleViolationError,
    NotFoundError
)
from app.core.events.dataclass.package import (
    PackageMediaAttachedEvent,
    PackageMediaRemovedEvent,
)
from app.dto import PackageMediaResponse
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)

def _publish_event(event: Any) -> None:
    from app.interface.package.services import event_bus
    event_bus.publish(event)

class PackageMediaService(BaseService):
    def __init__(
        self,
        package_repo: Any,
        media_repo: Any,       # PackageMediaRepository
        asset_repo: Any,       # MediaAssetRepository
        audit_service: Any,
        uow: Any,
    ) -> None:
        self._packages = package_repo
        self._media = media_repo
        self._assets = asset_repo
        self._audits = audit_service
        self._uow = uow

    def list_media(self, package_id: str) -> list[PackageMediaResponse]:
        if not self._packages.exists(id=package_id):
            raise NotFoundError("Package", package_id)
        # Fetch all media for this package
        rows = self._media.list_by(package_id=package_id)
        return [PackageMediaResponse.model_validate(r) for r in rows]

    def attach_media(
        self,
        package_id: str,
        asset_id: str,
        caption: str | None = None,
        itinerary_day_id: str | None = None,
        display_order: int = 0,
        actor_id: str | None = None,
        is_cover: bool = False
    ) -> PackageMediaResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            if not self._assets.exists(id=asset_id):
                raise NotFoundError("MediaAsset", asset_id)
            
            # Check if this asset is already attached to this package
            existing_stmt = self._media._session.query(self._media.model).filter_by(
                package_id=package_id, asset_id=asset_id, itinerary_day_id=itinerary_day_id
            )
            existing = existing_stmt.first()
            if existing:
                raise BusinessRuleViolationError("Media asset is already attached to this package.")

            if is_cover:
                # set_cover handles demoting existing cover
                row = self._media.set_cover(package_id=package_id, asset_id=asset_id, actor_id=actor_id)
            else:
                row = self._media.create(
                    actor_id=actor_id,
                    package_id=package_id,
                    asset_id=asset_id,
                    caption=caption,
                    itinerary_day_id=itinerary_day_id,
                    display_order=display_order,
                    is_cover=False
                )
            
            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Attached media asset {asset_id} to package.",
                after=self._snapshot(row, ["id", "asset_id", "is_cover"]),
                strict=True,
            )
            self._uow.commit()

        _publish_event(PackageMediaAttachedEvent(
            package_id=package_id,
            asset_id=asset_id,
            media_id=row.id,
            is_cover=row.is_cover,
            actor_id=actor_id
        ))
        
        return PackageMediaResponse.model_validate(row)

    def detach_media(self, package_media_id: str, actor_id: str | None = None) -> None:
        with self._uow:
            row = self._media.get(package_media_id)
            if not row:
                raise NotFoundError("PackageMedia", package_media_id)
            
            if row.is_cover:
                raise BusinessRuleViolationError("Cannot detach the cover image. Set another cover first.")

            package_id = row.package_id
            self._media.delete(row)
            
            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Detached media asset {row.asset_id} from package.",
                before=self._snapshot(row, ["id", "asset_id", "is_cover"]),
                strict=True,
            )
            self._uow.commit()

        _publish_event(PackageMediaRemovedEvent(
            package_id=package_id,
            media_id=package_media_id,
            actor_id=actor_id
        ))

    def set_cover(self, package_id: str, asset_id: str, actor_id: str | None = None) -> PackageMediaResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            if not self._assets.exists(id=asset_id):
                raise NotFoundError("MediaAsset", asset_id)

            row = self._media.set_cover(package_id=package_id, asset_id=asset_id, actor_id=actor_id)
            
            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Set media asset {asset_id} as cover image.",
                strict=True,
            )
            self._uow.commit()

        _publish_event(PackageMediaAttachedEvent(
            package_id=package_id,
            asset_id=asset_id,
            media_id=row.id,
            is_cover=True,
            actor_id=actor_id
        ))
        
        return PackageMediaResponse.model_validate(row)

    def reorder_gallery(self, package_id: str, ordered_ids: list[str], actor_id: str | None = None) -> None:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            
            gallery_media = {m.id: m for m in self._media.find_gallery(package_id)}
            for idx, mid in enumerate(ordered_ids):
                if mid in gallery_media:
                    self._media.update(gallery_media[mid], actor_id=actor_id, display_order=idx)
            
            self._uow.commit()
