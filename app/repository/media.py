from sqlalchemy import select as _mselect

from app.models import MediaAsset
from app.enums import  AssetType, AssetOwnerType
from app.repository.base import BaseRepository

class MediaAssetRepository(BaseRepository[MediaAsset]):
    model = MediaAsset

    def find_by_owner(
        self,
        owner_type: AssetOwnerType,
        owner_id: str,
        asset_type: AssetType | None = None,
    ) -> list[MediaAsset]:
        stmt = _mselect(MediaAsset).where(
            MediaAsset.owner_type == owner_type,
            MediaAsset.owner_id == owner_id,
        )
        if asset_type:
            stmt = stmt.where(MediaAsset.asset_type == asset_type)
        stmt = stmt.order_by(MediaAsset.created_at.desc())
        return list(self._session.execute(stmt).scalars().all())

    def find_by_storage_key(self, key: str) -> MediaAsset | None:
        return self.get_by(storage_key=key)

    def find_by_checksum(self, checksum: str) -> MediaAsset | None:
        return self.get_by(checksum_sha256=checksum)
