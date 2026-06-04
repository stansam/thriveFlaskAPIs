# app/interface/package/__init__.py
"""
PackageService Facade.

Composes modular sub-services for packages, items, pricing, media, and insurance,
while maintaining a consistent external integration layer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.enums import BookingStatus, PackageStatus
from app.dto import (
    PackageHighlightCreateRequest,
    PackageHighlightUpdateRequest,
    PackageHighlightResponse,
    PackageInclusionCreateRequest,
    PackageInclusionUpdateRequest,
    PackageInclusionResponse,
    PackageItineraryDayCreateRequest,
    PackageItineraryDayResponse,
    PackageItineraryDayUpdateRequest,
    PackagePriceTierCreateRequest,
    PackagePriceTierResponse,
    PackagePriceTierUpdateRequest,
    TravelPackageCreateRequest,
    TravelPackageResponse,
    TravelPackageUpdateRequest,
    PackageMediaResponse,
    PackageInsuranceCreateRequest,
    PackageInsuranceUpdateRequest,
    PackageInsuranceResponse,
)

from app.interface.package.services import (
    PackageCoreService,
    PackageItemsService,
    PackagePriceService,
    PackageMediaService,
    PackageInsuranceService,
)

from app.repository.package import TravelPackageRepository
from app.repository.package_items import (
    PackageHighlightRepository,
    PackageInclusionRepository,
    PackageItineraryDayRepository,
)
from app.repository.package_price import PackagePriceTierRepository
from app.repository.package_insurance import PackageInsuranceRepository
from app.repository.package_media import PackageMediaRepository
from app.repository.package_booking import PackageBookingRepository
from app.repository.media import MediaAssetRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork


class PackageService:
    """Service handling travel packages, pricing, items, media, and insurance."""

    def __init__(
        self,
        package_repo: TravelPackageRepository,
        package_highlight_repo: PackageHighlightRepository,
        package_inclusion_repo: PackageInclusionRepository,
        package_itinerary_day_repo: PackageItineraryDayRepository,
        package_price_tier_repo: PackagePriceTierRepository,
        package_insurance_repo: PackageInsuranceRepository,
        package_media_repo: PackageMediaRepository,
        package_booking_repo: PackageBookingRepository,
        media_asset_repo: MediaAssetRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        self._package_core = PackageCoreService(
            package_repo=package_repo,
            package_highlight_repo=package_highlight_repo,
            package_inclusion_repo=package_inclusion_repo,
            package_itinerary_day_repo=package_itinerary_day_repo,
            package_price_tier_repo=package_price_tier_repo,
            package_media_repo=package_media_repo,
            package_booking_repo=package_booking_repo,
            audit_service=audit_service,
            uow=uow
        )
        self._items = PackageItemsService(
            package_repo=package_repo,
            highlight_repo=package_highlight_repo,
            inclusion_repo=package_inclusion_repo,
            itinerary_repo=package_itinerary_day_repo,
            audit_service=audit_service,
            uow=uow
        )
        self._price = PackagePriceService(
            package_repo=package_repo,
            price_tier_repo=package_price_tier_repo,
            insurance_repo=package_insurance_repo,
            audit_service=audit_service,
            uow=uow
        )
        self._media = PackageMediaService(
            package_repo=package_repo,
            media_repo=package_media_repo,
            asset_repo=media_asset_repo,
            audit_service=audit_service,
            uow=uow
        )
        self._insurance = PackageInsuranceService(
            package_repo=package_repo,
            insurance_repo=package_insurance_repo,
            audit_service=audit_service,
            uow=uow
        )

    # Queries
    def get_package(self, package_id: str) -> TravelPackageResponse:
        return self._package_core.get(package_id)

    def get_package_by_slug(self, slug: str) -> TravelPackageResponse:
        return self._package_core.get_by_slug(slug)

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
    ) -> dict[str, Any]:
        return self._package_core.list(
            status=status,
            destination_country=destination_country,
            region=region,
            is_featured=is_featured,
            search=search,
            min_price=min_price,
            max_price=max_price,
            page=page,
            per_page=per_page
        )

    # CRUD
    def create_package(self, data: TravelPackageCreateRequest, actor_id: str) -> TravelPackageResponse:
        return self._package_core.create(data, actor_id)

    def update_package(self, package_id: str, data: TravelPackageUpdateRequest, actor_id: str) -> TravelPackageResponse:
        return self._package_core.update(package_id, data, actor_id)

    def publish_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        return self._package_core.publish(package_id, actor_id)

    def pause_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        return self._package_core.pause(package_id, actor_id)

    def archive_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        return self._package_core.archive(package_id, actor_id)

    def duplicate_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        return self._package_core.duplicate(package_id, actor_id)

    # Highlights
    def add_highlight(self, package_id: str, data: PackageHighlightCreateRequest, actor_id: str) -> PackageHighlightResponse:
        return self._items.add_highlight(package_id, data, actor_id)

    def update_highlight(self, highlight_id: str, data: PackageHighlightUpdateRequest, actor_id: str) -> PackageHighlightResponse:
        return self._items.update_highlight(highlight_id, data, actor_id)

    def delete_highlight(self, highlight_id: str, actor_id: str) -> None:
        self._items.delete_highlight(highlight_id, actor_id)

    def reorder_highlights(self, package_id: str, ordered_ids: list[str], actor_id: str) -> None:
        self._items.reorder_highlights(package_id, ordered_ids, actor_id)

    # Inclusions
    def add_inclusion(self, package_id: str, data: PackageInclusionCreateRequest, actor_id: str) -> PackageInclusionResponse:
        return self._items.add_inclusion(package_id, data, actor_id)

    def update_inclusion(self, inclusion_id: str, data: PackageInclusionUpdateRequest, actor_id: str) -> PackageInclusionResponse:
        return self._items.update_inclusion(inclusion_id, data, actor_id)

    def delete_inclusion(self, inclusion_id: str, actor_id: str) -> None:
        self._items.delete_inclusion(inclusion_id, actor_id)

    # Itineraries
    def add_itinerary_day(self, package_id: str, data: PackageItineraryDayCreateRequest, actor_id: str) -> PackageItineraryDayResponse:
        return self._items.add_itinerary_day(package_id, data, actor_id)

    def update_itinerary_day(self, day_id: str, data: PackageItineraryDayUpdateRequest, actor_id: str) -> PackageItineraryDayResponse:
        return self._items.update_itinerary_day(day_id, data, actor_id)

    def delete_itinerary_day(self, day_id: str, actor_id: str) -> None:
        self._items.delete_itinerary_day(day_id, actor_id)

    # Pricing
    def add_price_tier(self, package_id: str, data: PackagePriceTierCreateRequest, actor_id: str) -> PackagePriceTierResponse:
        return self._price.add_tier(package_id, data, actor_id)

    def update_price_tier(self, tier_id: str, data: PackagePriceTierUpdateRequest, actor_id: str) -> PackagePriceTierResponse:
        return self._price.update_tier(tier_id, data, actor_id)

    def deactivate_price_tier(self, tier_id: str, actor_id: str) -> None:
        self._price.deactivate_tier(tier_id, actor_id)

    def resolve_price_for_booking(self, package_id: str, num_participants: int, add_flight: bool = False, add_insurance: bool = False) -> Decimal:
        return self._price.resolve_price(package_id, num_participants, add_flight, add_insurance)

    # Media
    def list_media(self, package_id: str) -> list[PackageMediaResponse]:
        return self._media.list_media(package_id)

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
        return self._media.attach_media(package_id, asset_id, caption, itinerary_day_id, display_order, actor_id, is_cover)

    def detach_media(self, package_media_id: str, actor_id: str | None = None) -> None:
        self._media.detach_media(package_media_id, actor_id)

    def set_cover(self, package_id: str, asset_id: str, actor_id: str | None = None) -> PackageMediaResponse:
        return self._media.set_cover(package_id, asset_id, actor_id)

    def reorder_gallery(self, package_id: str, ordered_ids: list[str], actor_id: str | None = None) -> None:
        self._media.reorder_gallery(package_id, ordered_ids, actor_id)

    # Insurance
    def list_insurance(self, package_id: str) -> list[PackageInsuranceResponse]:
        return self._insurance.list_insurance(package_id)

    def add_insurance(self, package_id: str, data: PackageInsuranceCreateRequest, actor_id: str | None = None) -> PackageInsuranceResponse:
        return self._insurance.add_insurance(package_id, data, actor_id)

    def update_insurance(self, insurance_id: str, data: PackageInsuranceUpdateRequest, actor_id: str | None = None) -> PackageInsuranceResponse:
        return self._insurance.update_insurance(insurance_id, data, actor_id)

    def delete_insurance(self, insurance_id: str, actor_id: str | None = None) -> None:
        self._insurance.delete_insurance(insurance_id, actor_id)


__all__ = ["PackageService"]
