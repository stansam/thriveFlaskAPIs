from __future__ import annotations

from decimal import Decimal
from typing import Any
import uuid
from slugify import slugify
import logging

from app.enums import AuditActionType, BookingStatus, PackageStatus
from app.core.errors.handlers import (
    BadRequestError,
    BusinessRuleViolationError,
    DuplicateSlugError,
    NotFoundError
)
from app.core.events.dataclass.package import (
    PackageCreatedEvent,
    PackageUpdatedEvent,
    PackagePublishedEvent,
    PackagePausedEvent,
    PackageArchivedEvent,
    PackageDuplicatedEvent,
)
from app.dto import (
    TravelPackageCreateRequest,
    TravelPackageResponse,
    TravelPackageSummaryResponse,
    TravelPackageUpdateRequest,
    PackageMediaResponse,
)
from app.interface._base import BaseService
from app.core.logging import get_logger

logger = get_logger(__name__)

def _publish_event(event: Any) -> None:
    from app.interface.package.services import event_bus
    event_bus.publish(event)

def _build_package_response(pkg: Any) -> TravelPackageResponse:
    resp = TravelPackageResponse.model_validate(pkg)
    cover_row = None
    gallery_rows = []
    if hasattr(pkg, "media") and pkg.media:
        for m in pkg.media:
            if m.is_cover:
                cover_row = m
            elif m.itinerary_day_id is None:
                gallery_rows.append(m)
    
    if cover_row and cover_row.asset:
        resp.cover_image_url = cover_row.asset.cdn_url
    else:
        resp.cover_image_url = None
        
    resp.gallery = [PackageMediaResponse.model_validate(g) for g in gallery_rows]
    return resp

class PackageCoreService(BaseService):
    def __init__(
        self,
        package_repo: Any,
        package_highlight_repo: Any,
        package_inclusion_repo: Any,
        package_itinerary_day_repo: Any,
        package_price_tier_repo: Any,
        package_media_repo: Any,
        package_booking_repo: Any,
        audit_service: Any,
        uow: Any,
    ) -> None:
        self._packages = package_repo
        self._highlights = package_highlight_repo
        self._inclusions = package_inclusion_repo
        self._itineraries = package_itinerary_day_repo
        self._tiers = package_price_tier_repo
        self._media = package_media_repo
        self._bookings = package_booking_repo
        self._audits = audit_service
        self._uow = uow

    def get(self, package_id: str) -> TravelPackageResponse:
        pkg = self._packages.get(package_id)
        if not pkg:
            raise NotFoundError("Package", package_id)
        return _build_package_response(pkg)

    def get_by_slug(self, slug: str) -> TravelPackageResponse:
        pkg = self._packages.find_by_slug(slug)
        if not pkg:
            raise NotFoundError("Package", slug)
        return _build_package_response(pkg)

    def list(
        self,
        status: PackageStatus | None = None,
        destination_country: str | None = None,
        region: str | None = None,
        is_featured: bool | None = None,
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        result = self._packages.paginate_packages(
            status=status,
            destination_country=destination_country,
            region=region,
            is_featured=is_featured,
            search=search,
            min_price=min_price,
            max_price=max_price,
            page=page,
            per_page=per_page,
        )
        items = [TravelPackageSummaryResponse.model_validate(p) for p in result.items]
        for idx, item in enumerate(items):
            p = result.items[idx]
            cover_row = next((m for m in p.media if m.is_cover), None)
            if cover_row and cover_row.asset:
                item.cover_image_url = cover_row.asset.cdn_url
            else:
                item.cover_image_url = None
        return {"items": items, **self._page_meta(result)}

    def create(self, data: TravelPackageCreateRequest, actor_id: str) -> TravelPackageResponse:
        with self._uow:
            slug = data.slug or slugify(data.title)
            if self._packages.slug_exists(slug):
                slug = f"{slug}-{uuid.uuid4().hex[:6]}"

            pkg = self._packages.create(
                actor_id=actor_id,
                title=data.title,
                slug=slug,
                tagline=data.tagline,
                description=data.description,
                status=PackageStatus.DRAFT,
                destination_country=data.destination_country,
                destination_city=data.destination_city,
                region=data.region,
                duration_days=data.duration_days,
                duration_nights=data.duration_nights,
                base_price_usd=data.base_price_usd,
                price_per=data.price_per,
                min_participants=data.min_participants,
                max_participants=data.max_participants,
                flights_includable=data.flights_includable,
                insurance_includable=data.insurance_includable,
                is_featured=data.is_featured,
            )
            pkg_id = pkg.id

            if data.highlights:
                self._highlights.bulk_create(
                    [{**h.model_dump(), "package_id": pkg_id} for h in data.highlights],
                    actor_id=actor_id
                )
            if data.inclusions:
                self._inclusions.bulk_create(
                    [{**i.model_dump(), "package_id": pkg_id} for i in data.inclusions],
                    actor_id=actor_id
                )
            if data.itinerary:
                self._itineraries.bulk_create(
                    [{**day.model_dump(), "package_id": pkg_id} for day in data.itinerary],
                    actor_id=actor_id
                )
            if data.price_tiers:
                self._tiers.bulk_create(
                    [{**t.model_dump(), "package_id": pkg_id} for t in data.price_tiers],
                    actor_id=actor_id
                )

            self._audits.log(
                action=AuditActionType.CREATE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=pkg_id,
                description=f"Package '{data.title}' created.",
                after=self._snapshot(pkg, ["id", "title", "slug", "status"]),
                strict=True,
            )
            self._uow.commit()

        _publish_event(PackageCreatedEvent(
            package_id=pkg_id, title=data.title, actor_id=actor_id
        ))
        logger.info("Package created: %s (id=%s) by actor=%s", data.title, pkg_id, actor_id)

        pkg = self._packages.get(pkg_id)
        if not pkg:
            raise NotFoundError("Package", pkg_id)
        return _build_package_response(pkg)

    def update(self, package_id: str, data: TravelPackageUpdateRequest, actor_id: str) -> TravelPackageResponse:
        with self._uow:
            pkg = self._packages.get(package_id)
            if not pkg:
                raise NotFoundError("Package", package_id)
            before = self._snapshot(pkg)
            updates = data.model_dump(exclude_unset=True)

            if "title" in updates and "slug" not in updates:
                new_slug = slugify(updates["title"])
                if self._packages.slug_exists(new_slug, exclude_id=package_id):
                    new_slug = f"{new_slug}-{uuid.uuid4().hex[:6]}"
                updates["slug"] = new_slug

            if "slug" in updates:
                if self._packages.slug_exists(updates["slug"], exclude_id=package_id):
                    logger.warning("Update failed: Slug '%s' already in use for package %s", updates["slug"], package_id)
                    raise DuplicateSlugError(f"Slug '{updates['slug']}' is already in use.")

            if updates:
                self._packages.update(pkg, actor_id=actor_id, **updates)

            self._audits.log(
                action=AuditActionType.UPDATE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Package '{pkg.title}' updated: {list(updates.keys())}.",
                before=before,
                after=self._snapshot(pkg),
                strict=True,
            )
            self._uow.commit()

        _publish_event(PackageUpdatedEvent(
            package_id=package_id, actor_id=actor_id
        ))
        logger.info("Package updated: %s (id=%s) fields=%s by actor=%s", pkg.title, pkg.id, list(updates.keys()), actor_id)
        return _build_package_response(pkg)

    def publish(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        with self._uow:
            pkg = self._packages.get(package_id)
            if not pkg:
                raise NotFoundError("Package", package_id)
            
            if pkg.status not in (PackageStatus.DRAFT, PackageStatus.PAUSED):
                raise BusinessRuleViolationError(
                    f"Cannot publish package in {pkg.status.value} status."
                )

            errors: list[str] = []
            if not pkg.highlights:
                errors.append("Package must have at least one highlight.")
                
            tiers = self._tiers.find_by_package(package_id, active_only=True)
            if not tiers:
                errors.append("Package must have at least one active price tier.")
                
            cover = self._media.find_cover(package_id)
            if not cover:
                errors.append("Package must have a cover image.")

            if not pkg.itinerary_days:
                errors.append("Package must have at least one itinerary day.")
                
            if errors:
                logger.warning("Publish failed for Package %s: %s", package_id, "; ".join(errors))
                raise BadRequestError("Package cannot be published: " + "; ".join(errors))

            before_snapshot = self._snapshot(pkg, ["status"])

            self._packages.update(pkg, actor_id=actor_id, status=PackageStatus.ACTIVE)
            
            self._audits.log(
                action=AuditActionType.STATUS_CHANGE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Package '{pkg.title}' published.",
                before=before_snapshot,
                after={"status": PackageStatus.ACTIVE.value},
                strict=True,
            )
            self._uow.commit()

        _publish_event(PackagePublishedEvent(
            package_id=package_id, title=pkg.title, actor_id=actor_id
        ))
        logger.info("Package published: %s (id=%s) by actor=%s", pkg.title, pkg.id, actor_id)
        return _build_package_response(pkg)

    def pause(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        with self._uow:
            pkg = self._packages.get(package_id)
            if not pkg:
                raise NotFoundError("Package", package_id)
            
            if pkg.status != PackageStatus.ACTIVE:
                raise BusinessRuleViolationError(
                    f"Cannot pause package in {pkg.status.value} status."
                )

            before_snapshot = self._snapshot(pkg, ["status"])

            self._packages.update(pkg, actor_id=actor_id, status=PackageStatus.PAUSED)
            
            self._audits.log(
                action=AuditActionType.STATUS_CHANGE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Package '{pkg.title}' paused.",
                before=before_snapshot,
                after={"status": PackageStatus.PAUSED.value},
                strict=True,
            )
            self._uow.commit()

        _publish_event(PackagePausedEvent(
            package_id=package_id, actor_id=actor_id
        ))
        logger.info("Package paused: %s (id=%s) by actor=%s", pkg.title, pkg.id, actor_id)
        return _build_package_response(pkg)

    def archive(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        with self._uow:
            pkg = self._packages.get(package_id)
            if not pkg:
                raise NotFoundError("Package", package_id)
            
            future_bookings = self._bookings.find_by_package(
                package_id, status=BookingStatus.CONFIRMED
            )
            if future_bookings:
                raise BusinessRuleViolationError(
                    f"Cannot archive: package has {len(future_bookings)} confirmed future booking(s)."
                )
                
            before_snapshot = self._snapshot(pkg, ["status"])

            self._packages.update(pkg, actor_id=actor_id, status=PackageStatus.ARCHIVED)
            
            self._audits.log(
                action=AuditActionType.STATUS_CHANGE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Package '{pkg.title}' archived.",
                before=before_snapshot,
                after={"status": PackageStatus.ARCHIVED.value},
                strict=True,
            )
            self._uow.commit()

        _publish_event(PackageArchivedEvent(
            package_id=package_id, actor_id=actor_id
        ))
        logger.info("Package archived: %s (id=%s) by actor=%s", pkg.title, pkg.id, actor_id)
        return _build_package_response(pkg)

    def duplicate(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        with self._uow:
            src = self._packages.get(package_id)
            if not src:
                raise NotFoundError("Package", package_id)
            new_title = f"{src.title} (Copy)"
            new_slug  = slugify(new_title)
            
            if self._packages.slug_exists(new_slug):
                new_slug = f"{new_slug}-{uuid.uuid4().hex[:6]}"

            clone = self._packages.create(
                actor_id=actor_id,
                title=new_title,
                slug=new_slug,
                tagline=src.tagline,
                description=src.description,
                status=PackageStatus.DRAFT,
                destination_country=src.destination_country,
                destination_city=src.destination_city,
                region=src.region,
                duration_days=src.duration_days,
                duration_nights=src.duration_nights,
                base_price_usd=src.base_price_usd,
                price_per=src.price_per,
                min_participants=src.min_participants,
                max_participants=src.max_participants,
                flights_includable=src.flights_includable,
                insurance_includable=src.insurance_includable,
                is_featured=False,
            )
            for h in src.highlights:
                self._highlights.create(
                    actor_id=actor_id, package_id=clone.id,
                    text=h.text, icon=h.icon, display_order=h.display_order
                )
            for i in src.inclusions:
                self._inclusions.create(
                    actor_id=actor_id, package_id=clone.id,
                    inclusion_type=i.inclusion_type, label=i.label,
                    notes=i.notes, extra_cost_usd=i.extra_cost_usd,
                    display_order=i.display_order
                )
            
            day_mapping = {}
            for d in src.itinerary_days:
                new_day = self._itineraries.create(
                    actor_id=actor_id, package_id=clone.id,
                    day_number=d.day_number, title=d.title,
                    description=d.description, activities=d.activities,
                    meals_included=d.meals_included, accommodation=d.accommodation
                )
                day_mapping[d.id] = new_day.id

            for t in src.price_tiers:
                self._tiers.create(
                    actor_id=actor_id, package_id=clone.id,
                    label=t.label, price_usd=t.price_usd, price_per=t.price_per,
                    min_participants=t.min_participants, max_participants=t.max_participants,
                    is_add_on=t.is_add_on, is_active=t.is_active
                )

            for m in src.media:
                if not m.is_cover:
                    new_day_id = None
                    if m.itinerary_day_id and m.itinerary_day_id in day_mapping:
                        new_day_id = day_mapping[m.itinerary_day_id]
                    elif m.itinerary_day_id:
                        continue
                    
                    self._media.create(
                        actor_id=actor_id,
                        package_id=clone.id,
                        asset_id=m.asset_id,
                        itinerary_day_id=new_day_id,
                        is_cover=False,
                        display_order=m.display_order,
                        caption=m.caption
                    )

            self._audits.log(
                action=AuditActionType.CREATE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=clone.id,
                description=f"Package '{src.title}' duplicated → '{new_title}'.",
                strict=True,
            )
            self._uow.commit()

        _publish_event(PackageDuplicatedEvent(
            source_package_id=package_id, new_package_id=clone.id, new_title=new_title, actor_id=actor_id
        ))
        logger.info("Package duplicated: %s (id=%s) -> %s (id=%s) by actor=%s", src.title, src.id, new_title, clone.id, actor_id)
        
        pkg = self._packages.get(clone.id)
        if not pkg:
            raise NotFoundError("Package", clone.id)
        return _build_package_response(pkg)
