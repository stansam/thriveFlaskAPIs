from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import TravelClass, BookingStatus

class FlightBooking(BaseModel):
    __tablename__ = 'flight_bookings'

    booking_id = db.Column(db.String(36), db.ForeignKey('bookings.id'), nullable=False)
    
    pnr_reference = db.Column(db.String(20))
    eticket_number = db.Column(db.String(50))
    cabin_class = db.Column(db.Enum(TravelClass), default=TravelClass.ECONOMY)
    
    segments = db.relationship('Flight', backref='flight_booking', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FlightBooking {self.pnr_reference}>"


class Flight(BaseModel):
    __tablename__ = 'flights'
    
    flight_booking_id = db.Column(db.String(36), db.ForeignKey('flight_bookings.id'), nullable=False)
    
    carrier_code = db.Column(db.String(3), nullable=False)
    flight_number = db.Column(db.String(10), nullable=False)
    
    departure_airport_code = db.Column(db.String(3), nullable=False)
    arrival_airport_code = db.Column(db.String(3), nullable=False)
    
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    
    duration_minutes = db.Column(db.Integer)
    aircraft_type = db.Column(db.String(50))
    
    baggage_allowance = db.Column(db.String(100))
    terminal = db.Column(db.String(10))
    gate = db.Column(db.String(10))
    
    seat_assignment = db.Column(db.String(10))

    def __repr__(self):
        return f"<Flight {self.carrier_code}{self.flight_number} {self.departure_airport_code}->{self.arrival_airport_code}>"