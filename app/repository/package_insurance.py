from __future__ import annotations
from sqlalchemy import select

from app.models.package_insurance import PackageInsurance
from app.repository.base import BaseRepository

from app.core.logging import get_logger

logger = get_logger(__name__)

class PackageInsuranceRepository(BaseRepository[PackageInsurance]):
    model = PackageInsurance

    def find_by_package(
        self, package_id: str, active_only: bool = True
    ) -> list[PackageInsurance]:
        stmt = (
            select(PackageInsurance)
            .where(PackageInsurance.package_id == package_id)
        )
        if active_only:
            stmt = stmt.where(PackageInsurance.is_active.is_(True))
        return list(self._session.execute(stmt).scalars().all())
