from app.repository.base import BaseRepository
from app.models import PackageMedia

class PackageMediaRepository(BaseRepository[PackageMedia]):
    model = PackageMedia

    def find_cover(self, package_id: str) -> PackageMedia | None:
        stmt = select(PackageMedia).where(
            PackageMedia.package_id == package_id,
            PackageMedia.is_cover.is_(True),
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def find_gallery(self, package_id: str) -> list[PackageMedia]:
        stmt = (
            select(PackageMedia)
            .where(
                PackageMedia.package_id == package_id,
                PackageMedia.is_cover.is_(False),
                PackageMedia.itinerary_day_id.is_(None),
            )
            .order_by(PackageMedia.display_order)
        )
        return list(self._session.execute(stmt).scalars().all())

    def find_day_media(self, itinerary_day_id: str) -> list[PackageMedia]:
        stmt = (
            select(PackageMedia)
            .where(PackageMedia.itinerary_day_id == itinerary_day_id)
            .order_by(PackageMedia.display_order)
        )
        return list(self._session.execute(stmt).scalars().all())

    def set_cover(
        self,
        package_id: str,
        asset_id: str,
        actor_id: str | None = None,
    ) -> PackageMedia:
        """
        Promote one asset to cover, demoting any existing cover.
        Returns the new cover PackageMedia row.
        """
        # Demote existing cover
        existing = self.find_cover(package_id)
        if existing:
            self.update(existing, actor_id=actor_id, is_cover=False)

        # Find or create the target row
        stmt = select(PackageMedia).where(
            PackageMedia.package_id == package_id,
            PackageMedia.asset_id == asset_id,
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        if row:
            return self.update(row, actor_id=actor_id, is_cover=True, display_order=0)
        return self.create(
            actor_id=actor_id,
            package_id=package_id,
            asset_id=asset_id,
            is_cover=True,
            display_order=0,
        )
