from app.models import Package
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.package.exceptions import DatabaseError

class SearchPackages:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, filters: dict = None) -> list[Package]:
        try:
            query = self.db.query(Package).filter(Package.is_active == True)
            # TODO: Check on robustness
            if filters:
                if 'min_price' in filters:
                    query = query.filter(Package.base_price >= filters['min_price'])
                if 'max_price' in filters:
                     query = query.filter(Package.base_price <= filters['max_price'])
                if 'duration' in filters:
                     query = query.filter(Package.duration_days == filters['duration'])
                if 'keyword' in filters:
                    keyword = f"%{filters['keyword']}%"
                    query = query.filter(Package.title.ilike(keyword) | Package.description.ilike(keyword))

            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while searching packages: {str(e)}") from e
