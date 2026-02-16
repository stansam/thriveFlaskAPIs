from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import FeeType

class ServiceFeeRule(BaseModel):
    __tablename__ = 'service_fee_rules'
    
    name = db.Column(db.String(100), nullable=False)
    fee_type = db.Column(db.Enum(FeeType), nullable=False)
    
    amount_fixed = db.Column(db.Float, default=0.0)
    amount_percent = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    
    min_order_amount = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    
    priority = db.Column(db.Integer, default=0) 

    def __repr__(self):
        return f"<ServiceFeeRule {self.name} ({self.fee_type})>"
 