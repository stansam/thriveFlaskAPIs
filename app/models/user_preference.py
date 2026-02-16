from app.extensions import db
from app.models.base import BaseModel

class UserPreference(BaseModel):
    __tablename__ = "user_preferences"
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), unique=True, nullable=False)
    
    currency = db.Column(db.String(3), default="USD")
    language = db.Column(db.String(5), default="en")
    timezone = db.Column(db.String(50), default="UTC")
    
    marketing_opt_in = db.Column(db.Boolean, default=False)
    data_sharing_opt_in = db.Column(db.Boolean, default=False)
    
    email_updates = db.Column(db.Boolean, default=True)
    voice_notifications_enabled = db.Column(db.Boolean, default=False)
    # sms_updates = db.Column(db.Boolean, default=False)
    # whatsapp_updates = db.Column(db.Boolean, default=False)
    
    # preferred_seat = db.Column(db.String(20)) 
    # meal_preference = db.Column(db.String(50))

    def __repr__(self):
        return f"<UserPreference {self.user_id}>"