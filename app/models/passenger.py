from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import Gender

class Passenger(BaseModel):
    __tablename__ = 'passengers'

    booking_id = db.Column(db.String(36), db.ForeignKey('bookings.id'), nullable=False)
    
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum(Gender))
    
    passport_number = db.Column(db.String(50)) 
    passport_expiry = db.Column(db.Date)
    nationality = db.Column(db.String(50))
    
    special_requests = db.Column(db.Text)
    
    # TODO: Seat assignment 

    def __repr__(self):
        return f"<Passenger {self.first_name} {self.last_name}>"
