from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import PaymentStatus, PaymentMethod, SubscriptionTier

class Payment(BaseModel):
    __tablename__ = 'payments'
    
    booking_id = db.Column(db.String(36), db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False) 
    
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True) 
    
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_date = db.Column(db.DateTime)
    receipt_url = db.Column(db.String(255))


class Invoice(BaseModel):
    __tablename__ = 'invoices'
    
    booking_id = db.Column(db.String(36), db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    
    issued_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    
    total_amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    pdf_url = db.Column(db.String(255))
    status = db.Column(db.String(20), default='issued') 


class SubscriptionPlan(BaseModel):
    __tablename__ = 'subscription_plans'
    
    name = db.Column(db.String(50), nullable=False) 
    tier = db.Column(db.Enum(SubscriptionTier), unique=True, nullable=False)
    
    price_monthly = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    booking_limit_count = db.Column(db.Integer, default=0) 
    fee_waiver_rules = db.Column(db.JSON) 
    
    is_active = db.Column(db.Boolean, default=True)


class UserSubscription(BaseModel):
    __tablename__ = 'user_subscriptions'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=True) 
    
    plan_id = db.Column(db.String(36), db.ForeignKey('subscription_plans.id'), nullable=False)
    
    status = db.Column(db.String(20), default='active')
    
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    
    bookings_used_this_period = db.Column(db.Integer, default=0)
    auto_renew = db.Column(db.Boolean, default=True)