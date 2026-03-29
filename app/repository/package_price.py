from __future__ import annotations
from sqlalchemy import and_, or_, select

from app.models import PackagePriceTier
from app.repository.base import BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)


class PackagePriceTierRepository(BaseRepository[PackagePriceTier]):
    model = PackagePriceTier

    def find_by_package(
        self, package_id: str, active_only: bool = True
    ) -> list[PackagePriceTier]:
        stmt = (
            select(PackagePriceTier)
            .where(PackagePriceTier.package_id == package_id)
        )
        if active_only:
            stmt = stmt.where(PackagePriceTier.is_active.is_(True))
        stmt = stmt.order_by(PackagePriceTier.min_participants)
        return list(self._session.execute(stmt).scalars().all())

    def find_matching_tier(
        self,
        package_id: str,
        num_participants: int,
        is_add_on: bool = False,
    ) -> PackagePriceTier | None:
        """Return the price tier applicable for a given participant count."""
        stmt = (
            select(PackagePriceTier)
            .where(
                PackagePriceTier.package_id == package_id,
                PackagePriceTier.is_active.is_(True),
                PackagePriceTier.is_add_on.is_(is_add_on),
                PackagePriceTier.min_participants <= num_participants,
                or_(
                    PackagePriceTier.max_participants.is_(None),
                    PackagePriceTier.max_participants >= num_participants,
                ),
            )
            .order_by(PackagePriceTier.min_participants.desc())
            .limit(1)
        )
        return self._session.execute(stmt).scalar_one_or_none()
