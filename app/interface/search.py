# services/search_service.py
"""
SearchService — full-text search and autocomplete.

Implements interfaces.md § 14. SearchService.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.dto import BookingSummaryResponse, ClientSummaryResponse, TravelPackageSummaryResponse
from app.enums import PackageStatus
from app.repository import client_repo, booking_repo, package_repo
from app.interface._base import BaseService
from app.core.logging import get_logger
from app.core.dependencies import get_services

logger = get_logger(__name__)


@dataclass
class GlobalSearchResponse:
    clients:  list[ClientSummaryResponse] = field(default_factory=list)
    bookings: list[BookingSummaryResponse] = field(default_factory=list)
    packages: list[TravelPackageSummaryResponse] = field(default_factory=list)
    total: int = 0


class SearchService(BaseService):

    def global_search(self, query: str, limit: int = 10) -> GlobalSearchResponse:
        """
        Search across Clients, Bookings, and Packages simultaneously.

        For Clients: matches on name, email, phone.
        For Bookings: matches on reference_number.
        For Packages: matches on title, destination, tagline.
        """
        per_group = max(3, limit // 3)

        # Clients
        client_page = client_repo.paginate_clients(search=query, page=1, per_page=per_group)
        clients = [
            ClientSummaryResponse(
                id=c.id, full_name=c.full_name, email=c.email,
                phone=c.phone, whatsapp_number=c.whatsapp_number,
                client_type=c.client_type,
            )
            for c in client_page.items
        ]

        # Bookings (by reference number)
        booking = booking_repo.find_by_reference(query.upper().strip())
        bookings = []
        if booking:
            bookings.append(get_services().client.get_booking_summary(booking.id))

        # Fallback: paginate by reference prefix
        if not bookings:
            booking_page = booking_repo.paginate_bookings(search=query, page=1, per_page=per_group)
            bookings = [get_services().client.get_booking_summary(b.id) for b in booking_page.items]

        # Packages
        pkg_page = package_repo.paginate_packages(search=query, page=1, per_page=per_group)
        packages = [TravelPackageSummaryResponse.model_validate(p) for p in pkg_page.items]

        total = len(clients) + len(bookings) + len(packages)
        return GlobalSearchResponse(
            clients=clients, bookings=bookings, packages=packages, total=total
        )

    def autocomplete_client(self, query: str, limit: int = 10) -> list[ClientSummaryResponse]:
        page = client_repo.paginate_clients(search=query, page=1, per_page=min(limit, 20))
        return [
            ClientSummaryResponse(
                id=c.id, full_name=c.full_name, email=c.email,
                phone=c.phone, whatsapp_number=c.whatsapp_number,
                client_type=c.client_type,
            )
            for c in page.items
        ]

    def autocomplete_package(
        self, query: str, limit: int = 10
    ) -> list[TravelPackageSummaryResponse]:
        page = package_repo.paginate_packages(
            status=PackageStatus.ACTIVE, search=query, page=1, per_page=min(limit, 20)
        )
        return [TravelPackageSummaryResponse.model_validate(p) for p in page.items]


search_service = SearchService()