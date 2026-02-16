from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import SubscriptionTier

class Company(BaseModel):
    __tablename__ = 'companies'

    name = db.Column(db.String(100), nullable=False)
    tax_id = db.Column(db.String(50))
    address = db.Column(db.String(255))
    contact_email = db.Column(db.String(120))
    
    subscription_tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.NONE)
    subscription_status = db.Column(db.String(20), default='active')
    max_bookings_per_month = db.Column(db.Integer, default=0)
    
    employees = db.relationship('User', backref='company', lazy='dynamic')
    subscriptions = db.relationship('UserSubscription', backref='company', lazy='dynamic')

    def allowed_bookings(self):
        if self.subscription_tier == SubscriptionTier.BRONZE:
            return 6
        elif self.subscription_tier == SubscriptionTier.SILVER:
            return 15
        elif self.subscription_tier == SubscriptionTier.GOLD:
            return 9999
        return 0
