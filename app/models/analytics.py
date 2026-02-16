from app.extensions import db
from app.models.base import BaseModel

class AnalyticsMetric(BaseModel):
    __tablename__ = 'analytics_metrics'
    
    metric_name = db.Column(db.String(100), nullable=False, index=True)
    date_dimension = db.Column(db.Date, nullable=False, index=True)
    
    value = db.Column(db.Float, default=0.0)
    count = db.Column(db.Integer, default=0)
    
    category = db.Column(db.String(50)) 
    dimension_key = db.Column(db.String(100))
