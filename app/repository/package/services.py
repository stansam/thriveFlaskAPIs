from sqlalchemy.orm import Session
from app.models import Package
from app.repository.package.ops import (
    CreatePackage,
    SearchPackages,
    UpdatePackage,
    GetPackageByID
)

class PackageService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_package(self, package_data: dict) -> Package:
        return CreatePackage(self.db).execute(package_data)

    def get_package_by_id(self, package_id: str) -> Package:
        return GetPackageByID(self.db).execute(package_id)

    def search_packages(self, filters: dict = None) -> list[Package]:
        return SearchPackages(self.db).execute(filters)

    def update_package(self, package_id: str, updates: dict) -> Package:
        return UpdatePackage(self.db).execute(package_id, updates)
