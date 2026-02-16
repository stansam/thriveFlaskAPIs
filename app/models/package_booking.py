from app.extensions import db
from app.models.base import BaseModel

class PackageBooking(BaseModel):
    __tablename__ = 'package_bookings'
    
    booking_id = db.Column(db.String(36), db.ForeignKey('bookings.id'), nullable=False)
    package_id = db.Column(db.String(36), db.ForeignKey('packages.id'), nullable=True) 
    
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    number_of_adults = db.Column(db.Integer, default=1)
    number_of_children = db.Column(db.Integer, default=0)
    
    special_requests = db.Column(db.Text)
    
    custom_itinerary = db.relationship('CustomItinerary', backref='package_booking', uselist=False, cascade="all, delete-orphan")


class CustomItinerary(BaseModel):
    __tablename__ = 'custom_itineraries'
    
    booking_id = db.Column(db.String(36), db.ForeignKey('package_bookings.id'), nullable=False)
    title = db.Column(db.String(100), default="Custom Itinerary")
    start_date = db.Column(db.Date) 
    end_date = db.Column(db.Date)
    
    notes = db.Column(db.Text)
    approved_by_user = db.Column(db.Boolean, default=False)
    
    items = db.relationship('CustomItineraryItem', backref='custom_itinerary', lazy='dynamic', cascade="all, delete-orphan")


class CustomItineraryItem(BaseModel):
    __tablename__ = 'custom_itinerary_items'
    
    itinerary_id = db.Column(db.String(36), db.ForeignKey('custom_itineraries.id'), nullable=False)
    day_number = db.Column(db.Integer)
    time = db.Column(db.Time)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    type = db.Column(db.String(50)) 
    reference_id = db.Column(db.String(36))
    cost = db.Column(db.Float)