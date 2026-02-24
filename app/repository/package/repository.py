from typing import Optional, List
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models.package import Package
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.package.utils import build_package_search_filters

class PackageRepository(BaseRepository[Package]):
    """
    PackageRepository encapsulating complex product lookups, eager nested
    relationship fetching, and dynamic search filter application.
    """

    def __init__(self):
        super().__init__(Package)

    @handle_db_exceptions
    def search_packages(self, filters: dict, limit: int = 50, offset: int = 0) -> List[Package]:
        """Provides dynamic SQL filtering spanning country, city, and duration."""
        query = self.model.query.filter_by(is_active=True)
        
        # Apply deterministic filter building rules based on user input dict
        filter_conditions = build_package_search_filters(self.model, filters)
        for condition in filter_conditions:
            query = query.filter(condition)
            
        return query.limit(limit).offset(offset).all()

    @handle_db_exceptions
    def get_featured_packages(self, limit: int = 10) -> List[Package]:
        return self.model.query.filter_by(
            is_featured=True, 
            is_active=True
        ).limit(limit).all()

    @handle_db_exceptions
    def get_package_with_full_details(self, package_id: str) -> Optional[Package]:
        """Eagerly loads deeply nested one-to-many relationship structures."""
        return self.model.query.options(
            joinedload(self.model.itineraries),
            joinedload(self.model.inclusions),
            joinedload(self.model.media)
        ).filter_by(id=package_id, is_active=True).first()

    @handle_db_exceptions
    def get_package_by_slug(self, slug: str) -> Optional[Package]:
        """Lookup an active package using its SEO-friendly URL slug."""
        return self.model.query.filter_by(slug=slug.lower(), is_active=True).first()
