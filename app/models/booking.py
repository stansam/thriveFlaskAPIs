from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import BookingStatus, BookingType

class Booking(BaseModel):
    __tablename__ = 'bookings'

    reference_code = db.Column(db.String(12), unique=True, nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    booking_type = db.Column(db.Enum(BookingType), nullable=False)
    
    total_amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    
    notes = db.Column(db.Text)
    
    passengers = db.relationship('Passenger', backref='booking', lazy='dynamic', cascade="all, delete-orphan")
    payments = db.relationship('Payment', backref='booking', lazy='dynamic')
    invoices = db.relationship('Invoice', backref='booking', lazy='dynamic')
    
    flight_booking = db.relationship('FlightBooking', backref='booking', uselist=False, cascade="all, delete-orphan")
    package_booking = db.relationship('PackageBooking', backref='booking', uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Booking {self.reference_code}>"
