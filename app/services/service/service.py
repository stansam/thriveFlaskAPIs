from typing import List
from app.repository.registry import repositories
from app.models.services import Service

class ServicesService:
    def __init__(self):
        self.service_repo = repositories.service

    def create_service(self, service: dict) -> Service:
        return self.service_repo.create(service)

    def get_all_services(self) -> List[Service]:
        return self.service_repo.get_all()

    def update_service(self, service_id: str, service: dict) -> Service:
        return self.service_repo.update(service_id, service)

    def delete_service(self, service_id: str) -> Service:
        return self.service_repo.delete(service_id)
    
    def bulk_insert_services(self, services: List[dict]) -> List[Service]:
        return self.service_repo.bulk_insert_services(services)