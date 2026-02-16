from app.extensions import db
from app.models.base import BaseModel

class Package(BaseModel):
    __tablename__ = 'packages'
    
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, index=True)
    description = db.Column(db.Text)
    
    base_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    duration_days = db.Column(db.Integer, nullable=False)
    
    is_active = db.Column(db.Boolean, default=True)
    featured_image_url = db.Column(db.String(255))
    gallery_urls = db.Column(db.JSON) 
    
    itinerary = db.relationship('PackageItinerary', backref='package', lazy='dynamic', cascade="all, delete-orphan", order_by="PackageItinerary.day_number")
    inclusions = db.relationship('PackageInclusion', backref='package', lazy='dynamic', cascade="all, delete-orphan")


class PackageItinerary(BaseModel):
    __tablename__ = 'package_itineraries'
    
    package_id = db.Column(db.String(36), db.ForeignKey('packages.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    activity_type = db.Column(db.String(50)) 


class PackageInclusion(BaseModel):
    __tablename__ = 'package_inclusions'
    
    package_id = db.Column(db.String(36), db.ForeignKey('packages.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    is_included = db.Column(db.Boolean, default=True) 