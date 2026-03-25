# repositories/package_repository.py
"""
Repositories for TravelPackage and PackageMedia.
"""

from __future__ import annotations

from sqlalchemy import and_, or_, select

from app.models import TravelPackage
from app.enums import PackageStatus
from .base import BaseRepository, Page

class TravelPackageRepository(BaseRepository[TravelPackage]):
    model = TravelPackage

    def find_by_slug(self, slug: str) -> TravelPackage | None:
        stmt = select(TravelPackage).where(TravelPackage.slug == slug)
        return self._session.execute(stmt).scalar_one_or_none()

    def find_by_slug_or_404(self, slug: str) -> TravelPackage:
        from werkzeug.exceptions import NotFound
        pkg = self.find_by_slug(slug)
        if pkg is None:
            raise NotFound(f"Package '{slug}' not found.")
        return pkg

    def find_active(self) -> list[TravelPackage]:
        stmt = (
            select(TravelPackage)
            .where(TravelPackage.status == PackageStatus.ACTIVE)
            .order_by(TravelPackage.is_featured.desc(), TravelPackage.created_at.desc())
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_featured(self) -> list[TravelPackage]:
        stmt = (
            select(TravelPackage)
            .where(
                TravelPackage.status == PackageStatus.ACTIVE,
                TravelPackage.is_featured.is_(True),
            )
            .order_by(TravelPackage.title)
        )
        return list(self._session.execute(stmt).scalars().all())

    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool:
        stmt = select(TravelPackage).where(TravelPackage.slug == slug)
        if exclude_id:
            stmt = stmt.where(TravelPackage.id != exclude_id)
        return self._session.execute(stmt).scalar_one_or_none() is not None

    def paginate_packages(
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
    ) -> Page[TravelPackage]:
        stmt = select(TravelPackage)
        if status is not None:
            stmt = stmt.where(TravelPackage.status == status)
        if destination_country:
            stmt = stmt.where(
                TravelPackage.destination_country.ilike(f"%{destination_country}%")
            )
        if region:
            stmt = stmt.where(TravelPackage.region.ilike(f"%{region}%"))
        if is_featured is not None:
            stmt = stmt.where(TravelPackage.is_featured.is_(is_featured))
        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    TravelPackage.title.ilike(term),
                    TravelPackage.destination_city.ilike(term),
                    TravelPackage.destination_country.ilike(term),
                    TravelPackage.tagline.ilike(term),
                )
            )
        if min_price is not None:
            stmt = stmt.where(TravelPackage.base_price_usd >= min_price)
        if max_price is not None:
            stmt = stmt.where(TravelPackage.base_price_usd <= max_price)
        stmt = stmt.order_by(
            TravelPackage.is_featured.desc(),
            TravelPackage.created_at.desc(),
        )
        return self.paginate(stmt, page=page, per_page=per_page)

