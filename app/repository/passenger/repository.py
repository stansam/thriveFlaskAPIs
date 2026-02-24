from typing import List
from app.extensions import db
from app.models.passenger import Passenger
from app.repository.base.repository import BaseRepository
from app.repository.base.utils import handle_db_exceptions
from app.repository.passenger.utils import validate_passenger_payload

class PassengerRepository(BaseRepository[Passenger]):
    """
    PassengerRepository managing the records of travelers attached to specific
    group bookings or enterprise accounts.
    """

    def __init__(self):
        super().__init__(Passenger)

    @handle_db_exceptions
    def bulk_insert_passengers(self, passengers_data: List[dict]) -> List[Passenger]:
        """
        Bypasses standard SQLAlchemy object iteration caching in favor of raw 
        compiled SQL inserts, vastly accelerating processing of massive group bookings.
        """
        # Strictly evaluate formats before bulk dumping into PostgreSQL
        validated_data = [validate_passenger_payload(p) for p in passengers_data]
        
        # Core SQLAlchemy 2.0+ bulk insert mappings logic
        db.session.bulk_insert_mappings(self.model, validated_data)
        db.session.commit()
        
        # We query them back out purely if the caller instantly needs the generated IDs.
        # Alternatively, returning just a success boolean is faster if IDs aren't needed yet.
        booking_ids = list(set([p.get('booking_id') for p in validated_data if p.get('booking_id')]))
        if booking_ids:
             return self.model.query.filter(self.model.booking_id.in_(booking_ids)).all()
        return []

    @handle_db_exceptions
    def get_passengers_for_booking(self, booking_id: str) -> List[Passenger]:
        """Fetch all individual travelers linked to a unified booking ledger."""
        return self.model.query.filter_by(booking_id=booking_id).all()
