from models import PackageHighlight, PackageInclusion, PackageItineraryDay
from app.repository.base import BaseRepository

class PackageHighlightRepository(BaseRepository[PackageHighlight]):
    model = PackageHighlight

    def find_by_package(self, package_id: str) -> list[PackageHighlight]:
        stmt = (
            select(PackageHighlight)
            .where(PackageHighlight.package_id == package_id)
            .order_by(PackageHighlight.display_order)
        )
        return list(self._session.execute(stmt).scalars().all())

    def reorder(
        self,
        package_id: str,
        ordered_ids: list[str],
        actor_id: str | None = None,
    ) -> None:
        """Set display_order on a list of highlight IDs in sequence."""
        highlights = {h.id: h for h in self.find_by_package(package_id)}
        for idx, hid in enumerate(ordered_ids):
            if hid in highlights:
                self.update(highlights[hid], actor_id=actor_id, display_order=idx)

class PackageInclusionRepository(BaseRepository[PackageInclusion]):
    model = PackageInclusion

    def find_by_package(self, package_id: str) -> list[PackageInclusion]:
        stmt = (
            select(PackageInclusion)
            .where(PackageInclusion.package_id == package_id)
            .order_by(PackageInclusion.inclusion_type, PackageInclusion.display_order)
        )
        return list(self._session.execute(stmt).scalars().all())

class PackageItineraryDayRepository(BaseRepository[PackageItineraryDay]):
    model = PackageItineraryDay

    def find_by_package_ordered(self, package_id: str) -> list[PackageItineraryDay]:
        stmt = (
            select(PackageItineraryDay)
            .where(PackageItineraryDay.package_id == package_id)
            .order_by(PackageItineraryDay.day_number)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_day(self, package_id: str, day_number: int) -> PackageItineraryDay | None:
        stmt = select(PackageItineraryDay).where(
            PackageItineraryDay.package_id == package_id,
            PackageItineraryDay.day_number == day_number,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def max_day_number(self, package_id: str) -> int:
        from sqlalchemy import func
        stmt = (
            select(func.max(PackageItineraryDay.day_number))
            .where(PackageItineraryDay.package_id == package_id)
        )
        result = self._session.execute(stmt).scalar_one_or_none()
        return result or 0