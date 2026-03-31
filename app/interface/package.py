# services/package_service.py
"""
PackageService — travel package catalogue management.

Implements interfaces.md § 5. PackageService.
"""

from __future__ import annotations

from decimal import Decimal

from slugify import slugify

from app.models.base import db
from app.enums import AuditActionType,BookingStatus,PackageStatus
from app.core.errors.handlers import (
    BadRequestError,
    BusinessRuleViolationError,
    DuplicateSlugError,
)
from app.core.events import event_bus
from app.core.events.dataclass import PackagePublishedEvent
from app.core.logging import get_logger
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
from app.repository import (
    package_repo,
    package_highlight_repo,
    package_inclusion_repo,
    package_itinerary_day_repo,
    package_price_tier_repo,
    package_media_repo,
    package_booking_repo,
)
from app.interface._base import BaseService

logger = get_logger(__name__)


class PackageService(BaseService):
    # Queries
    def get_package(self, package_id: str) -> TravelPackageResponse:
        pkg = package_repo.get_or_404(package_id)
        return _build_package_response(pkg)

    def get_package_by_slug(self, slug: str) -> TravelPackageResponse:
        pkg = package_repo.find_by_slug_or_404(slug)
        return _build_package_response(pkg)

    def list_packages(
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
    ) -> dict:
        result = package_repo.paginate_packages(
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
    # Package CRUD
    def create_package(
        self, data: TravelPackageCreateRequest, actor_id: str
    ) -> TravelPackageResponse:
        slug = data.slug or slugify(data.title)
        if package_repo.slug_exists(slug):
            slug = f"{slug}-{__import__('uuid').uuid4().hex[:6]}"

        pkg = package_repo.create(
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
            package_highlight_repo.create(
                actor_id=actor_id, package_id=pkg.id, **h.model_dump()
            )
        for i in data.inclusions:
            package_inclusion_repo.create(
                actor_id=actor_id, package_id=pkg.id, **i.model_dump()
            )
        for idx, day in enumerate(data.itinerary):
            package_itinerary_day_repo.create(
                actor_id=actor_id, package_id=pkg.id, **day.model_dump()
            )
        for t in data.price_tiers:
            package_price_tier_repo.create(
                actor_id=actor_id, package_id=pkg.id, **t.model_dump()
            )

        self._audit(
            action=AuditActionType.CREATE,
            actor_id=actor_id,
            entity_type="travel_package",
            entity_id=pkg.id,
            description=f"Package '{data.title}' created.",
            after=self._snapshot(pkg, ["id", "title", "slug", "status"]),
        )
        db.session.commit()
        return _build_package_response(pkg)

    def update_package(
        self, package_id: str, data: TravelPackageUpdateRequest, actor_id: str
    ) -> TravelPackageResponse:
        pkg = package_repo.get_or_404(package_id)
        before = self._snapshot(pkg)
        updates = data.model_dump(exclude_none=True)

        if "title" in updates and "slug" not in updates:
            new_slug = slugify(updates["title"])
            if package_repo.slug_exists(new_slug, exclude_id=package_id):
                new_slug = f"{new_slug}-{__import__('uuid').uuid4().hex[:6]}"
            updates["slug"] = new_slug

        if "slug" in updates:
            if package_repo.slug_exists(updates["slug"], exclude_id=package_id):
                raise DuplicateSlugError(f"Slug '{updates['slug']}' is already in use.")

        if updates:
            package_repo.update(pkg, actor_id=actor_id, **updates)

        self._audit(
            action=AuditActionType.UPDATE,
            actor_id=actor_id,
            entity_type="travel_package",
            entity_id=package_id,
            description=f"Package '{pkg.title}' updated: {list(updates.keys())}.",
            before=before,
            after=self._snapshot(pkg),
        )
        db.session.commit()
        return _build_package_response(pkg)

    def publish_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        pkg = package_repo.get_or_404(package_id)
        errors: list[str] = []
        if not pkg.highlights:
            errors.append("Package must have at least one highlight.")
        tiers = package_price_tier_repo.find_by_package(package_id, active_only=True)
        if not tiers:
            errors.append("Package must have at least one active price tier.")
        cover = package_media_repo.find_cover(package_id)
        if not cover:
            errors.append("Package must have a cover image.")
        if errors:
            raise BadRequestError(
                "Package cannot be published: " + "; ".join(errors)
            )

        package_repo.update(pkg, actor_id=actor_id, status=PackageStatus.ACTIVE)
        self._audit(
            action=AuditActionType.STATUS_CHANGE,
            actor_id=actor_id,
            entity_type="travel_package",
            entity_id=package_id,
            description=f"Package '{pkg.title}' published.",
            before={"status": PackageStatus.DRAFT.value},
            after={"status": PackageStatus.ACTIVE.value},
        )
        db.session.commit()
        event_bus.publish(PackagePublishedEvent(
            package_id=package_id, title=pkg.title, actor_id=actor_id
        ))
        return _build_package_response(pkg)

    def pause_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        pkg = package_repo.get_or_404(package_id)
        package_repo.update(pkg, actor_id=actor_id, status=PackageStatus.PAUSED)
        self._audit(AuditActionType.STATUS_CHANGE, actor_id, "travel_package",
                    package_id, f"Package '{pkg.title}' paused.")
        db.session.commit()
        return _build_package_response(pkg)

    def archive_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        pkg = package_repo.get_or_404(package_id)
        future_bookings = package_booking_repo.find_by_package(
            package_id, status=BookingStatus.CONFIRMED
        )
        if future_bookings:
            raise BusinessRuleViolationError(
                f"Cannot archive: package has {len(future_bookings)} confirmed future booking(s)."
            )
        package_repo.update(pkg, actor_id=actor_id, status=PackageStatus.ARCHIVED)
        self._audit(AuditActionType.STATUS_CHANGE, actor_id, "travel_package",
                    package_id, f"Package '{pkg.title}' archived.")
        db.session.commit()
        return _build_package_response(pkg)

    def duplicate_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        """Deep-clone a package into a new DRAFT."""
        src = package_repo.get_or_404(package_id)
        new_title = f"{src.title} (Copy)"
        new_slug  = slugify(new_title)
        if package_repo.slug_exists(new_slug):
            new_slug = f"{new_slug}-{__import__('uuid').uuid4().hex[:6]}"

        clone = package_repo.create(
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
            package_highlight_repo.create(
                actor_id=actor_id, package_id=clone.id,
                text=h.text, icon=h.icon, display_order=h.display_order
            )
        for i in src.inclusions:
            package_inclusion_repo.create(
                actor_id=actor_id, package_id=clone.id,
                inclusion_type=i.inclusion_type, label=i.label,
                notes=i.notes, extra_cost_usd=i.extra_cost_usd,
                display_order=i.display_order
            )
        for d in src.itinerary_days:
            package_itinerary_day_repo.create(
                actor_id=actor_id, package_id=clone.id,
                day_number=d.day_number, title=d.title,
                description=d.description, activities=d.activities,
                meals_included=d.meals_included, accommodation=d.accommodation
            )
        for t in src.price_tiers:
            package_price_tier_repo.create(
                actor_id=actor_id, package_id=clone.id,
                label=t.label, price_usd=t.price_usd, price_per=t.price_per,
                min_participants=t.min_participants, max_participants=t.max_participants,
                is_add_on=t.is_add_on, is_active=t.is_active
            )

        self._audit(AuditActionType.CREATE, actor_id, "travel_package",
                    clone.id, f"Package '{src.title}' duplicated → '{new_title}'.")
        db.session.commit()
        return _build_package_response(clone)
    # Highlights
    def add_highlight(
        self, package_id: str, data: PackageHighlightCreateRequest, actor_id: str
    ) -> PackageHighlightResponse:
        package_repo.get_or_404(package_id)
        max_order = package_highlight_repo.count(
            __import__("sqlalchemy").select(
                __import__("models.package", fromlist=["PackageHighlight"]).PackageHighlight
            ).where(
                __import__("models.package", fromlist=["PackageHighlight"]).PackageHighlight.package_id == package_id
            )
        )
        h = package_highlight_repo.create(
            actor_id=actor_id, package_id=package_id,
            text=data.text, icon=data.icon, display_order=max_order
        )
        db.session.commit()
        return PackageHighlightResponse.model_validate(h)

    def update_highlight(
        self, highlight_id: str, data: dict, actor_id: str
    ) -> PackageHighlightResponse:
        h = package_highlight_repo.get_or_404(highlight_id)
        package_highlight_repo.update(h, actor_id=actor_id, **{
            k: v for k, v in data.items() if v is not None
        })
        db.session.commit()
        return PackageHighlightResponse.model_validate(h)

    def delete_highlight(self, highlight_id: str, actor_id: str) -> None:
        h = package_highlight_repo.get_or_404(highlight_id)
        package_highlight_repo.delete(h)
        db.session.commit()

    def reorder_highlights(
        self, package_id: str, ordered_ids: list[str], actor_id: str
    ) -> None:
        package_highlight_repo.reorder(package_id, ordered_ids, actor_id=actor_id)
        db.session.commit()
    # Inclusions
    def add_inclusion(
        self, package_id: str, data: PackageInclusionCreateRequest, actor_id: str
    ) -> PackageInclusionResponse:
        package_repo.get_or_404(package_id)
        inc = package_inclusion_repo.create(
            actor_id=actor_id, package_id=package_id, **data.model_dump()
        )
        db.session.commit()
        return PackageInclusionResponse.model_validate(inc)

    def update_inclusion(
        self, inclusion_id: str, data: dict, actor_id: str
    ) -> PackageInclusionResponse:
        inc = package_inclusion_repo.get_or_404(inclusion_id)
        package_inclusion_repo.update(inc, actor_id=actor_id, **{
            k: v for k, v in data.items() if v is not None
        })
        db.session.commit()
        return PackageInclusionResponse.model_validate(inc)

    def delete_inclusion(self, inclusion_id: str, actor_id: str) -> None:
        inc = package_inclusion_repo.get_or_404(inclusion_id)
        package_inclusion_repo.delete(inc)
        db.session.commit()
    # Itinerary days
    def add_itinerary_day(
        self, package_id: str, data: PackageItineraryDayCreateRequest, actor_id: str
    ) -> PackageItineraryDayResponse:
        package_repo.get_or_404(package_id)
        expected = package_itinerary_day_repo.max_day_number(package_id) + 1
        if data.day_number != expected:
            raise BadRequestError(
                f"Day number must be sequential. Expected day {expected}, got {data.day_number}."
            )
        day = package_itinerary_day_repo.create(
            actor_id=actor_id, package_id=package_id, **data.model_dump()
        )
        db.session.commit()
        return PackageItineraryDayResponse.model_validate(day)

    def update_itinerary_day(
        self, day_id: str, data: PackageItineraryDayUpdateRequest, actor_id: str
    ) -> PackageItineraryDayResponse:
        day = package_itinerary_day_repo.get_or_404(day_id)
        updates = data.model_dump(exclude_none=True)
        if updates:
            package_itinerary_day_repo.update(day, actor_id=actor_id, **updates)
        db.session.commit()
        return PackageItineraryDayResponse.model_validate(day)

    def delete_itinerary_day(self, day_id: str, actor_id: str) -> None:
        day = package_itinerary_day_repo.get_or_404(day_id)
        package_itinerary_day_repo.delete(day)
        db.session.commit()
    # Price tiers
    def add_price_tier(
        self, package_id: str, data: PackagePriceTierCreateRequest, actor_id: str
    ) -> PackagePriceTierResponse:
        package_repo.get_or_404(package_id)
        # Validate no overlap in active tiers
        existing = package_price_tier_repo.find_by_package(package_id, active_only=True)
        for ex in existing:
            if not ex.is_add_on and not data.is_add_on:
                overlap = (
                    data.min_participants <= (ex.max_participants or 9999)
                    and (data.max_participants or 9999) >= ex.min_participants
                )
                if overlap:
                    raise BadRequestError(
                        f"Tier participant range overlaps with existing tier '{ex.label}'."
                    )
        tier = package_price_tier_repo.create(
            actor_id=actor_id, package_id=package_id, **data.model_dump()
        )
        db.session.commit()
        return PackagePriceTierResponse.model_validate(tier)

    def update_price_tier(
        self, tier_id: str, data: PackagePriceTierUpdateRequest, actor_id: str
    ) -> PackagePriceTierResponse:
        tier = package_price_tier_repo.get_or_404(tier_id)
        updates = data.model_dump(exclude_none=True)
        if updates:
            package_price_tier_repo.update(tier, actor_id=actor_id, **updates)
        db.session.commit()
        return PackagePriceTierResponse.model_validate(tier)

    def deactivate_price_tier(self, tier_id: str, actor_id: str) -> None:
        tier = package_price_tier_repo.get_or_404(tier_id)
        package_price_tier_repo.update(tier, actor_id=actor_id, is_active=False)
        db.session.commit()

    def resolve_price_for_booking(
        self,
        package_id: str,
        num_participants: int,
        add_flight: bool = False,
        add_insurance: bool = False,
    ) -> Decimal:
        tier = package_price_tier_repo.find_matching_tier(package_id, num_participants)
        if not tier:
            raise BadRequestError(
                f"No active price tier found for {num_participants} participant(s)."
            )
        total = tier.price_usd * num_participants

        if add_flight:
            flight_tier = package_price_tier_repo.find_matching_tier(
                package_id, num_participants, is_add_on=True
            )
            if flight_tier:
                total += flight_tier.price_usd * num_participants

        return total

# Helper
def _build_package_response(pkg) -> TravelPackageResponse:
    resp = TravelPackageResponse.model_validate(pkg)
    cover = None
    cover_row = pkg.media[0] if hasattr(pkg, "media") and pkg.media else None
    if cover_row and cover_row.is_cover:
        resp.cover_image_url = cover_row.asset.cdn_url if cover_row.asset else None
    return resp


package_service = PackageService()