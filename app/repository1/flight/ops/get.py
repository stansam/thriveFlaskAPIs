from app.models import Flight
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.repository.flight.exceptions import FlightNotFound, DatabaseError

class GetFlightByID:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, flight_id: str) -> Flight:
        try:
            flight = self.db.query(Flight).filter_by(id=flight_id).first()
            if not flight:
                raise FlightNotFound(f"Flight with ID {flight_id} not found")
            return flight
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error while fetching flight: {str(e)}") from e
