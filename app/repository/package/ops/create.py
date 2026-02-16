from app.models import Package, PackageItinerary, PackageInclusion
from app.models.enums import ActivityType
from app.extensions import db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import uuid
from app.repository.package.exceptions import DatabaseError, InvalidPackageData

class CreatePackage:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, package_data: dict) -> Package:
        try:
            # Extract nested data
            itinerary_data = package_data.pop('itinerary', [])
            inclusions_data = package_data.pop('inclusions', [])
            
            # Generate slug if not provided (simple version)
            if 'slug' not in package_data:
                package_data['slug'] = f"{package_data['title'].lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"

            new_package = Package(**package_data)
            
            self.db.add(new_package)
            self.db.flush() # get ID
            
            # Add Itinerary Items
            for item in itinerary_data:
                if 'activity_type' in item and isinstance(item['activity_type'], str):
                     try:
                        item['activity_type'] = ActivityType(item['activity_type'])
                     except ValueError:
                        raise InvalidPackageData(f"Invalid activity type: {item['activity_type']}")

                itinerary_item = PackageItinerary(package_id=new_package.id, **item)
                self.db.add(itinerary_item)
                
            # Add Inclusions
            for item in inclusions_data:
                inclusion = PackageInclusion(package_id=new_package.id, **item)
                self.db.add(inclusion)

            self.db.commit()
            self.db.refresh(new_package)
            return new_package

        except IntegrityError:
            self.db.rollback()
            raise InvalidPackageData("Package slug or title constraint violation")
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error while creating package: {str(e)}") from e
