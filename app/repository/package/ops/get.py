from app.models import Package
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.package.exceptions import PackageNotFound, DatabaseError

class GetPackageByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, package_id: str) -> Package:
        try:
            package = self.db.query(Package).filter_by(id=package_id).first()
            if not package:
                raise PackageNotFound(f"Package with ID {package_id} not found")
            return package
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching package: {str(e)}") from e
