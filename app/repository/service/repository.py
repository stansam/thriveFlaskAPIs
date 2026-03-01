from typing import List
from app.extensions import db
from app.models.service import Service
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.service.utils import validate_service_payload

class ServiceRepository(BaseRepository[Service]):
    """
    ServiceRepository managing the records of services attached to specific
    group bookings or enterprise accounts.
    """

    def __init__(self):
        super().__init__(Service)

    @handle_db_exceptions
    def bulk_insert_services(self, services_data: List[dict]) -> List[Service]:
        """
        Bypasses standard SQLAlchemy object iteration caching in favor of raw 
        compiled SQL inserts, vastly accelerating processing of massive group bookings.
        """
        validated_data = [validate_service_payload(p) for p in services_data]
        
        db.session.bulk_insert_mappings(self.model, validated_data)
        db.session.commit()
        
        # Query them back out purely if the caller instantly needs the generated IDs.
        service_ids = list(set([p.get('id') for p in validated_data if p.get('id')]))
        if service_ids:
            return self.model.query.filter(self.model.id.in_(service_ids)).all()
        return []



