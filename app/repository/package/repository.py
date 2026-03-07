from typing import Optional, List, Tuple
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models.package import Package
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions

class PackageRepository(BaseRepository[Package]):
    """
    PackageRepository encapsulating complex product lookups, eager nested
    relationship fetching, and dynamic search filter application.
    """

    def __init__(self):
        super().__init__(Package)

    @handle_db_exceptions
    def search_packages(self, filters: dict, limit: int = 50, offset: int = 0) -> Tuple[List[Package], int]:
        """Provides dynamic SQL filtering spanning country, city, duration, and price."""
        from sqlalchemy import or_
        from app.models.package_price import PackagePricingSeason, PackagePricing

        query = self.model.query.filter_by(is_active=True)
        
        if filters.get('q'):
            term = f"%{filters['q']}%"
            query = query.filter(or_(
                self.model.title.ilike(term),
                self.model.description.ilike(term),
                self.model.city.ilike(term),
                self.model.country.ilike(term)
            ))
            
        if filters.get('country'):
            query = query.filter(self.model.country.ilike(f"%{filters['country']}%"))
            
        if filters.get('min_days'):
            query = query.filter(self.model.duration_days >= int(filters['min_days']))
            
        if filters.get('max_days'):
            query = query.filter(self.model.duration_days <= int(filters['max_days']))

        if filters.get('min_price') is not None or filters.get('max_price') is not None:
             query = query.join(PackagePricingSeason, self.model.id == PackagePricingSeason.package_id) \
                          .join(PackagePricing, PackagePricingSeason.id == PackagePricing.season_id)
             if filters.get('min_price') is not None:
                 query = query.filter(PackagePricing.adult_price >= float(filters['min_price']))
             if filters.get('max_price') is not None:
                 query = query.filter(PackagePricing.adult_price <= float(filters['max_price']))
                 
        query = query.distinct()
        
        total = query.count()
        items = query.limit(limit).offset(offset).all()
        return items, total

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
