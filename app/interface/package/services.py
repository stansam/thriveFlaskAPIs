# app/interface/package/services.py
"""
Package Service Operations.

Strict, single-responsibility CQRS-style classes encapsulating all
travel package components (Highlights, Inclusions, Pricing Tiers, Itineraries).
Implements explicit UoW controls locking execution safely while emitting dynamic lifecycle events structurally.
"""

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
)
from app.core.events import event_bus
from app.core.events.dataclass.package import (
    PackageCreatedEvent,
    PackageUpdatedEvent,
    PackagePublishedEvent,
    PackagePausedEvent,
    PackageArchivedEvent,
    PackageDuplicatedEvent,
    PackageHighlightAddedEvent,
    PackageHighlightUpdatedEvent,
    PackageHighlightDeletedEvent,
    PackageInclusionAddedEvent,
    PackageInclusionUpdatedEvent,
    PackageInclusionDeletedEvent,
    PackageItineraryDayAddedEvent,
    PackageItineraryDayUpdatedEvent,
    PackageItineraryDayDeletedEvent,
    PackagePriceTierAddedEvent,
    PackagePriceTierUpdatedEvent,
    PackagePriceTierDeactivatedEvent,
)
from app.dto import (
    PackageHighlightCreateRequest,
    PackageHighlightResponse,
    PackageInclusionCreateRequest,
    PackageInclusionResponse,
    PackageItineraryDayCreateRequest,
    PackageItineraryDayResponse,
    PackageItineraryDayUpdateRequest,
    PackagePriceTierCreateRequest,
    PackagePriceTierResponse,
    PackagePriceTierUpdateRequest,
    TravelPackageCreateRequest,
    TravelPackageResponse,
    TravelPackageSummaryResponse,
    TravelPackageUpdateRequest,
)
from app.interface._base import BaseService
from app.core.logging import get_logger

logger: logging.Logger = get_logger(__name__)

# Helper
def _build_package_response(pkg: Any) -> TravelPackageResponse:
    resp = TravelPackageResponse.model_validate(pkg)
    cover_row = pkg.media[0] if hasattr(pkg, "media") and pkg.media else None
    if cover_row and hasattr(cover_row, "is_cover") and cover_row.is_cover:
        resp.cover_image_url = cover_row.asset.cdn_url if cover_row.asset else None
    return resp


class _PackageOperation(BaseService):
    """
    Base operation dynamically routing the 7 nested repository injections.
    """
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


# ── Queries ──
class GetPackageOperation(_PackageOperation):
    def execute(self, package_id: str) -> TravelPackageResponse:
        pkg = self._packages.get(package_id)
        if not pkg:
            raise NotFoundError("Package", package_id)
        return _build_package_response(pkg)


class GetPackageBySlugOperation(_PackageOperation):
    def execute(self, slug: str) -> TravelPackageResponse:
        pkg = self._packages.find_by_slug(slug)
        if not pkg:
            raise NotFoundError("Package", slug)
        return _build_package_response(pkg)


class ListPackagesOperation(_PackageOperation):
    def execute(
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
        return {"items": items, **self._page_meta(result)}


# ── Core Package Mutations ──
class CreatePackageOperation(_PackageOperation):
    def execute(self, data: TravelPackageCreateRequest, actor_id: str) -> TravelPackageResponse:
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
                status=data.status,
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

            for h in data.highlights:
                self._highlights.create(actor_id=actor_id, package_id=pkg.id, **h.model_dump())
            for i in data.inclusions:
                self._inclusions.create(actor_id=actor_id, package_id=pkg.id, **i.model_dump())
            for idx, day in enumerate(data.itinerary):
                self._itineraries.create(actor_id=actor_id, package_id=pkg.id, **day.model_dump())
            for t in data.price_tiers:
                self._tiers.create(actor_id=actor_id, package_id=pkg.id, **t.model_dump())

            self._audits.log(
                action=AuditActionType.CREATE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=pkg.id,
                description=f"Package '{data.title}' created.",
                after=self._snapshot(pkg, ["id", "title", "slug", "status"]),
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(PackageCreatedEvent(
            package_id=pkg.id, title=pkg.title, actor_id=actor_id
        ))
        logger.info("Package created: %s (id=%s) by actor=%s", pkg.title, pkg.id, actor_id)
        
        # We need to reload the entity post-commit to return the full DTO structure
        pkg = self._packages.get(pkg.id)
        if not pkg:
            raise NotFoundError("Package", pkg.id)
        return _build_package_response(pkg)


class UpdatePackageOperation(_PackageOperation):
    def execute(self, package_id: str, data: TravelPackageUpdateRequest, actor_id: str) -> TravelPackageResponse:
        with self._uow:
            pkg = self._packages.get(package_id)
            if not pkg:
                raise NotFoundError("Package", package_id)
            before = self._snapshot(pkg)
            updates = data.model_dump(exclude_none=True)

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

        event_bus.publish(PackageUpdatedEvent(
            package_id=package_id, actor_id=actor_id
        ))
        logger.info("Package updated: %s (id=%s) fields=%s by actor=%s", pkg.title, pkg.id, list(updates.keys()), actor_id)
        return _build_package_response(pkg)


class PublishPackageOperation(_PackageOperation):
    def execute(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        with self._uow:
            pkg = self._packages.get(package_id)
            if not pkg:
                raise NotFoundError("Package", package_id)
            errors: list[str] = []
            
            if not pkg.highlights:
                errors.append("Package must have at least one highlight.")
                
            tiers = self._tiers.find_by_package(package_id, active_only=True)
            if not tiers:
                errors.append("Package must have at least one active price tier.")
                
            cover = self._media.find_cover(package_id)
            if not cover:
                errors.append("Package must have a cover image.")
                
            if errors:
                logger.warning("Publish failed for Package %s: %s", package_id, "; ".join(errors))
                raise BadRequestError("Package cannot be published: " + "; ".join(errors))

            self._packages.update(pkg, actor_id=actor_id, status=PackageStatus.ACTIVE)
            
            self._audits.log(
                action=AuditActionType.STATUS_CHANGE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Package '{pkg.title}' published.",
                before={"status": PackageStatus.DRAFT.value},
                after={"status": PackageStatus.ACTIVE.value},
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(PackagePublishedEvent(
            package_id=package_id, title=pkg.title, actor_id=actor_id
        ))
        logger.info("Package published: %s (id=%s) by actor=%s", pkg.title, pkg.id, actor_id)
        return _build_package_response(pkg)


class PausePackageOperation(_PackageOperation):
    def execute(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        with self._uow:
            pkg = self._packages.get(package_id)
            if not pkg:
                raise NotFoundError("Package", package_id)
            self._packages.update(pkg, actor_id=actor_id, status=PackageStatus.PAUSED)
            
            self._audits.log(
                action=AuditActionType.STATUS_CHANGE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Package '{pkg.title}' paused.",
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(PackagePausedEvent(
            package_id=package_id, actor_id=actor_id
        ))
        logger.info("Package paused: %s (id=%s) by actor=%s", pkg.title, pkg.id, actor_id)
        return _build_package_response(pkg)


class ArchivePackageOperation(_PackageOperation):
    def execute(self, package_id: str, actor_id: str) -> TravelPackageResponse:
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
                
            self._packages.update(pkg, actor_id=actor_id, status=PackageStatus.ARCHIVED)
            
            self._audits.log(
                action=AuditActionType.STATUS_CHANGE,
                actor_id=actor_id,
                entity_type="travel_package",
                entity_id=package_id,
                description=f"Package '{pkg.title}' archived.",
                strict=True,
            )
            self._uow.commit()

        event_bus.publish(PackageArchivedEvent(
            package_id=package_id, actor_id=actor_id
        ))
        logger.info("Package archived: %s (id=%s) by actor=%s", pkg.title, pkg.id, actor_id)
        return _build_package_response(pkg)


class DuplicatePackageOperation(_PackageOperation):
    def execute(self, package_id: str, actor_id: str) -> TravelPackageResponse:
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
            for d in src.itinerary_days:
                self._itineraries.create(
                    actor_id=actor_id, package_id=clone.id,
                    day_number=d.day_number, title=d.title,
                    description=d.description, activities=d.activities,
                    meals_included=d.meals_included, accommodation=d.accommodation
                )
            for t in src.price_tiers:
                self._tiers.create(
                    actor_id=actor_id, package_id=clone.id,
                    label=t.label, price_usd=t.price_usd, price_per=t.price_per,
                    min_participants=t.min_participants, max_participants=t.max_participants,
                    is_add_on=t.is_add_on, is_active=t.is_active
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

        event_bus.publish(PackageDuplicatedEvent(
            source_package_id=package_id, new_package_id=clone.id, new_title=new_title, actor_id=actor_id
        ))
        logger.info("Package duplicated: %s (id=%s) -> %s (id=%s) by actor=%s", src.title, src.id, new_title, clone.id, actor_id)
        
        pkg = self._packages.get(clone.id)
        if not pkg:
            raise NotFoundError("Package", clone.id)
        return _build_package_response(pkg)


# ── Highlights ──
class AddHighlightOperation(_PackageOperation):
    def execute(self, package_id: str, data: PackageHighlightCreateRequest, actor_id: str) -> PackageHighlightResponse:
        from sqlalchemy import select
        from app.models import PackageHighlight
        
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            stmt = select(PackageHighlight).where(PackageHighlight.package_id == package_id)
            max_order = self._highlights.count(stmt)
            
            h = self._highlights.create(
                actor_id=actor_id, package_id=package_id,
                text=data.text, icon=data.icon, display_order=max_order
            )
            self._uow.commit()

        event_bus.publish(PackageHighlightAddedEvent(package_id=package_id, highlight_id=h.id, actor_id=actor_id))
        return PackageHighlightResponse.model_validate(h)


class UpdateHighlightOperation(_PackageOperation):
    def execute(self, highlight_id: str, data: dict[str, Any], actor_id: str) -> PackageHighlightResponse:
        with self._uow:
            h = self._highlights.get(highlight_id)
            if not h:
                raise NotFoundError("Package Highlight", highlight_id)
            self._highlights.update(h, actor_id=actor_id, **{k: v for k, v in data.items() if v is not None})
            self._uow.commit()

        event_bus.publish(PackageHighlightUpdatedEvent(highlight_id=h.id, actor_id=actor_id))
        return PackageHighlightResponse.model_validate(h)


class DeleteHighlightOperation(_PackageOperation):
    def execute(self, highlight_id: str, actor_id: str) -> None:
        with self._uow:
            h = self._highlights.get(highlight_id)
            if not h:
                raise NotFoundError("Package Highlight", highlight_id)
            self._highlights.delete(h)
            self._uow.commit()
            
        event_bus.publish(PackageHighlightDeletedEvent(highlight_id=highlight_id, actor_id=actor_id))


class ReorderHighlightsOperation(_PackageOperation):
    def execute(self, package_id: str, ordered_ids: list[str], actor_id: str) -> None:
        with self._uow:
            self._highlights.reorder(package_id, ordered_ids, actor_id=actor_id)
            self._uow.commit()


# ── Inclusions ──
class AddInclusionOperation(_PackageOperation):
    def execute(self, package_id: str, data: PackageInclusionCreateRequest, actor_id: str) -> PackageInclusionResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            inc = self._inclusions.create(
                actor_id=actor_id, package_id=package_id, **data.model_dump()
            )
            self._uow.commit()

        event_bus.publish(PackageInclusionAddedEvent(package_id=package_id, inclusion_id=inc.id, actor_id=actor_id))
        return PackageInclusionResponse.model_validate(inc)


class UpdateInclusionOperation(_PackageOperation):
    def execute(self, inclusion_id: str, data: dict[str, Any], actor_id: str) -> PackageInclusionResponse:
        with self._uow:
            inc = self._inclusions.get(inclusion_id)
            if not inc:
                raise NotFoundError("Package Inclusion", inclusion_id)
            self._inclusions.update(inc, actor_id=actor_id, **{k: v for k, v in data.items() if v is not None})
            self._uow.commit()

        event_bus.publish(PackageInclusionUpdatedEvent(inclusion_id=inc.id, actor_id=actor_id))
        return PackageInclusionResponse.model_validate(inc)


class DeleteInclusionOperation(_PackageOperation):
    def execute(self, inclusion_id: str, actor_id: str) -> None:
        with self._uow:
            inc = self._inclusions.get(inclusion_id)
            if not inc:
                raise NotFoundError("Package Inclusion", inclusion_id)
            self._inclusions.delete(inc)
            self._uow.commit()
            
        event_bus.publish(PackageInclusionDeletedEvent(inclusion_id=inclusion_id, actor_id=actor_id))


# ── Itinerary Days ──
class AddItineraryDayOperation(_PackageOperation):
    def execute(self, package_id: str, data: PackageInineraryDayCreateRequest, actor_id: str) -> PackageInineraryDayResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            expected = self._itineraries.max_day_number(package_id) + 1
            if data.day_number != expected:
                raise BadRequestError(
                    f"Day number must be sequential. Expected day {expected}, got {data.day_number}."
                )
            day = self._itineraries.create(
                actor_id=actor_id, package_id=package_id, **data.model_dump()
            )
            self._uow.commit()
            
        event_bus.publish(PackageItineraryDayAddedEvent(package_id=package_id, day_id=day.id, actor_id=actor_id))
        PackageItineraryDayResponse.model_rebuild()
        return PackageItineraryDayResponse.model_validate(day)


class UpdateItineraryDayOperation(_PackageOperation):
    def execute(self, day_id: str, data: PackageInineraryDayUpdateRequest, actor_id: str) -> PackageInineraryDayResponse:
        with self._uow:
            day = self._itineraries.get(day_id)
            if not day:
                raise NotFoundError("Package Itinerary Day", day_id)
            updates = data.model_dump(exclude_none=True)
            if updates:
                self._itineraries.update(day, actor_id=actor_id, **updates)
            self._uow.commit()
            
        event_bus.publish(PackageItineraryDayUpdatedEvent(day_id=day.id, actor_id=actor_id))
        PackageItineraryDayResponse.model_rebuild()
        return PackageItineraryDayResponse.model_validate(day)


class DeleteItineraryDayOperation(_PackageOperation):
    def execute(self, day_id: str, actor_id: str) -> None:
        with self._uow:
            day = self._itineraries.get(day_id)
            if not day:
                raise NotFoundError("Package Itinerary Day", day_id)
            self._itineraries.delete(day)
            self._uow.commit()
            
        event_bus.publish(PackageItineraryDayDeletedEvent(day_id=day_id, actor_id=actor_id))


# ── Price Tiers ──
class AddPriceTierOperation(_PackageOperation):
    def execute(self, package_id: str, data: PackagePriceTierCreateRequest, actor_id: str) -> PackagePriceTierResponse:
        with self._uow:
            if not self._packages.exists(id=package_id):
                raise NotFoundError("Package", package_id)
            existing = self._tiers.find_by_package(package_id, active_only=True)
            for ex in existing:
                if not ex.is_add_on and not data.is_add_on:
                    overlap = (
                        data.min_participants <= (ex.max_participants or 9999)
                        and (data.max_participants or 9999) >= ex.min_participants
                    )
                    if overlap:
                        raise BadRequestError(f"Tier participant range overlaps with existing tier '{ex.label}'.")
            
            tier = self._tiers.create(
                actor_id=actor_id, package_id=package_id, **data.model_dump()
            )
            self._uow.commit()
            
        event_bus.publish(PackagePriceTierAddedEvent(package_id=package_id, tier_id=tier.id, actor_id=actor_id))
        return PackagePriceTierResponse.model_validate(tier)


class UpdatePriceTierOperation(_PackageOperation):
    def execute(self, tier_id: str, data: PackagePriceTierUpdateRequest, actor_id: str) -> PackagePriceTierResponse:
        with self._uow:
            tier = self._tiers.get(tier_id)
            if not tier:
                raise NotFoundError("Package Price Tier", tier_id)
            updates = data.model_dump(exclude_none=True)
            if updates:
                self._tiers.update(tier, actor_id=actor_id, **updates)
            self._uow.commit()
            
        event_bus.publish(PackagePriceTierUpdatedEvent(tier_id=tier.id, actor_id=actor_id))
        return PackagePriceTierResponse.model_validate(tier)


class DeactivatePriceTierOperation(_PackageOperation):
    def execute(self, tier_id: str, actor_id: str) -> None:
        with self._uow:
            tier = self._tiers.get(tier_id)
            if not tier:
                raise NotFoundError("Package Price Tier", tier_id)
            self._tiers.update(tier, actor_id=actor_id, is_active=False)
            self._uow.commit()

        event_bus.publish(PackagePriceTierDeactivatedEvent(tier_id=tier_id, actor_id=actor_id))


class ResolvePriceForBookingOperation(_PackageOperation):
    def execute(self, package_id: str, num_participants: int, add_flight: bool = False, add_insurance: bool = False) -> Decimal:
        tier = self._tiers.find_matching_tier(package_id, num_participants)
        if not tier:
            raise BadRequestError(f"No active price tier found for {num_participants} participant(s).")
            
        total = tier.price_usd * num_participants

        if add_flight:
            flight_tier = self._tiers.find_matching_tier(package_id, num_participants, is_add_on=True) # Usually mapped inside matching dynamically.
            if flight_tier:
                total += flight_tier.price_usd * num_participants

        return total
