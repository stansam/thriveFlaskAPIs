# app/interface/package/__init__.py
"""
PackageService Facade.

Composes strictly separated CQRS-like operations framing
the massive monolithic Package boundaries dynamically internally
while matching external usage integrations properly natively.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.enums import BookingStatus, PackageStatus
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
    TravelPackageUpdateRequest,
)

from app.interface.package.services import (
    GetPackageOperation,
    GetPackageBySlugOperation,
    ListPackagesOperation,
    CreatePackageOperation,
    UpdatePackageOperation,
    PublishPackageOperation,
    PausePackageOperation,
    ArchivePackageOperation,
    DuplicatePackageOperation,
    AddHighlightOperation,
    UpdateHighlightOperation,
    DeleteHighlightOperation,
    ReorderHighlightsOperation,
    AddInclusionOperation,
    UpdateInclusionOperation,
    DeleteInclusionOperation,
    AddItineraryDayOperation,
    UpdateItineraryDayOperation,
    DeleteItineraryDayOperation,
    AddPriceTierOperation,
    UpdatePriceTierOperation,
    DeactivatePriceTierOperation,
    ResolvePriceForBookingOperation,
)

from app.repository.package import TravelPackageRepository
from app.repository.package_items import (
    PackageHighlightRepository,
    PackageInclusionRepository,
    PackageItineraryDayRepository,
)
from app.repository.package_price import PackagePriceTierRepository
from app.repository.package_media import PackageMediaRepository
from app.repository.package_booking import PackageBookingRepository
from app.interface.audit import AuditService
from app.core.unit_of_work import IUnitOfWork


class PackageService:
    """Service handling multi-tenant travel package deployments scaling.

    Responsibilities
    ----------------
    - CRUD over root packaging instances and slugs securely.
    - Deep updates resolving structural nested properties safely.
    - Enforced Atomic commits trapping audits completely organically.

    Dependencies
    ------------
    package_repo, package_highlight_repo, package_inclusion_repo,
    package_itinerary_day_repo, package_price_tier_repo, package_media_repo,
    package_booking_repo, audit_service, uow
    """

    def __init__(
        self,
        package_repo: TravelPackageRepository,
        package_highlight_repo: PackageHighlightRepository,
        package_inclusion_repo: PackageInclusionRepository,
        package_itinerary_day_repo: PackageItineraryDayRepository,
        package_price_tier_repo: PackagePriceTierRepository,
        package_media_repo: PackageMediaRepository,
        package_booking_repo: PackageBookingRepository,
        audit_service: AuditService,
        uow: IUnitOfWork,
    ) -> None:
        args = (
            package_repo,
            package_highlight_repo,
            package_inclusion_repo,
            package_itinerary_day_repo,
            package_price_tier_repo,
            package_media_repo,
            package_booking_repo,
            audit_service,
            uow,
        )
        
        self._get_op = GetPackageOperation(*args)
        self._get_slug_op = GetPackageBySlugOperation(*args)
        self._list_op = ListPackagesOperation(*args)
        self._create_op = CreatePackageOperation(*args)
        self._update_op = UpdatePackageOperation(*args)
        self._publish_op = PublishPackageOperation(*args)
        self._pause_op = PausePackageOperation(*args)
        self._archive_op = ArchivePackageOperation(*args)
        self._duplicate_op = DuplicatePackageOperation(*args)
        self._add_highlight_op = AddHighlightOperation(*args)
        self._update_highlight_op = UpdateHighlightOperation(*args)
        self._delete_highlight_op = DeleteHighlightOperation(*args)
        self._reorder_highlight_op = ReorderHighlightsOperation(*args)
        self._add_inclusion_op = AddInclusionOperation(*args)
        self._update_inclusion_op = UpdateInclusionOperation(*args)
        self._delete_inclusion_op = DeleteInclusionOperation(*args)
        self._add_itinerary_day_op = AddItineraryDayOperation(*args)
        self._update_itinerary_day_op = UpdateItineraryDayOperation(*args)
        self._delete_itinerary_day_op = DeleteItineraryDayOperation(*args)
        self._add_price_tier_op = AddPriceTierOperation(*args)
        self._update_price_tier_op = UpdatePriceTierOperation(*args)
        self._deactivate_price_tier_op = DeactivatePriceTierOperation(*args)
        self._resolve_price_op = ResolvePriceForBookingOperation(*args)

    # Queries
    def get_package(self, package_id: str) -> TravelPackageResponse:
        return self._get_op.execute(package_id)

    def get_package_by_slug(self, slug: str) -> TravelPackageResponse:
        return self._get_slug_op.execute(slug)

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
        return self._list_op.execute(
            status, destination_country, region, is_featured, search, min_price, max_price, page, per_page
        )

    # CRUD
    def create_package(self, data: TravelPackageCreateRequest, actor_id: str) -> TravelPackageResponse:
        return self._create_op.execute(data, actor_id)

    def update_package(self, package_id: str, data: TravelPackageUpdateRequest, actor_id: str) -> TravelPackageResponse:
        return self._update_op.execute(package_id, data, actor_id)

    def publish_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        return self._publish_op.execute(package_id, actor_id)

    def pause_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        return self._pause_op.execute(package_id, actor_id)

    def archive_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        return self._archive_op.execute(package_id, actor_id)

    def duplicate_package(self, package_id: str, actor_id: str) -> TravelPackageResponse:
        return self._duplicate_op.execute(package_id, actor_id)

    # Highlights
    def add_highlight(self, package_id: str, data: PackageHighlightCreateRequest, actor_id: str) -> PackageHighlightResponse:
        return self._add_highlight_op.execute(package_id, data, actor_id)

    def update_highlight(self, highlight_id: str, data: dict[str, Any], actor_id: str) -> PackageHighlightResponse:
        return self._update_highlight_op.execute(highlight_id, data, actor_id)

    def delete_highlight(self, highlight_id: str, actor_id: str) -> None:
        self._delete_highlight_op.execute(highlight_id, actor_id)

    def reorder_highlights(self, package_id: str, ordered_ids: list[str], actor_id: str) -> None:
        self._reorder_highlight_op.execute(package_id, ordered_ids, actor_id)

    # Inclusions
    def add_inclusion(self, package_id: str, data: PackageInclusionCreateRequest, actor_id: str) -> PackageInclusionResponse:
        return self._add_inclusion_op.execute(package_id, data, actor_id)

    def update_inclusion(self, inclusion_id: str, data: dict[str, Any], actor_id: str) -> PackageInclusionResponse:
        return self._update_inclusion_op.execute(inclusion_id, data, actor_id)

    def delete_inclusion(self, inclusion_id: str, actor_id: str) -> None:
        self._delete_inclusion_op.execute(inclusion_id, actor_id)

    # Itineraries
    def add_itinerary_day(self, package_id: str, data: PackageItineraryDayCreateRequest, actor_id: str) -> PackageItineraryDayResponse:
        return self._add_itinerary_day_op.execute(package_id, data, actor_id)

    def update_itinerary_day(self, day_id: str, data: PackageItineraryDayUpdateRequest, actor_id: str) -> PackageItineraryDayResponse:
        return self._update_itinerary_day_op.execute(day_id, data, actor_id)

    def delete_itinerary_day(self, day_id: str, actor_id: str) -> None:
        self._delete_itinerary_day_op.execute(day_id, actor_id)

    # Pricing
    def add_price_tier(self, package_id: str, data: PackagePriceTierCreateRequest, actor_id: str) -> PackagePriceTierResponse:
        return self._add_price_tier_op.execute(package_id, data, actor_id)

    def update_price_tier(self, tier_id: str, data: PackagePriceTierUpdateRequest, actor_id: str) -> PackagePriceTierResponse:
        return self._update_price_tier_op.execute(tier_id, data, actor_id)

    def deactivate_price_tier(self, tier_id: str, actor_id: str) -> None:
        self._deactivate_price_tier_op.execute(tier_id, actor_id)

    def resolve_price_for_booking(self, package_id: str, num_participants: int, add_flight: bool = False, add_insurance: bool = False) -> Decimal:
        return self._resolve_price_op.execute(package_id, num_participants, add_flight, add_insurance)
