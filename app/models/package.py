from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import ActivityType, OccupancyType

class Package(BaseModel):
    __tablename__ = 'packages'
    
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, index=True)
    
    description = db.Column(db.Text)
    highlights = db.Column(db.JSON)
    
    duration_nights = db.Column(db.Integer, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)

    country = db.Column(db.String(100))
    city = db.Column(db.String(100))

    currency = db.Column(db.String(3), default='USD')
    
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    
    itineraries = db.relationship('PackageItinerary', backref='package', lazy='dynamic', cascade="all, delete-orphan")
    inclusions = db.relationship('PackageInclusion', backref='package', lazy='dynamic', cascade="all, delete-orphan")
    media = db.relationship("PackageMedia", cascade="all, delete-orphan")
    departures = db.relationship('PackageDeparture', backref='package', lazy='dynamic', cascade="all, delete-orphan")
    pricing_seasons = db.relationship('PackagePricingSeason', backref='package', lazy='dynamic', cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "duration_nights": self.duration_nights,
            "duration_days": self.duration_days,
            "country": self.country,
            "city": self.city,
            "currency": self.currency,
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "media": [
                {
                    "image_url": m.image_url,
                    "is_featured": m.is_featured,
                    "display_order": m.display_order
                } for m in self.media
            ],
            "itineraries": [
                {
                    "day_number": i.day_number,
                    "title": i.title,
                    "description": i.description,
                    "location": i.location
                } for i in self.itineraries
            ],
            "inclusions": [
                {
                    "description": inc.description,
                    "is_included": inc.is_included
                } for inc in self.inclusions
            ]
        }

    def __repr__(self):
        return f"<Package {self.title} ({self.slug})>"


class PackageItinerary(BaseModel):
    __tablename__ = 'package_itineraries'
    
    package_id = db.Column(db.String(36), db.ForeignKey('packages.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    # activity_type = db.Column(db.Enum(ActivityType))

    def __repr__(self):
        return f"<PackageItinerary Day {self.day_number} - {self.title}>"


class PackageInclusion(BaseModel):
    __tablename__ = 'package_inclusions'
    
    package_id = db.Column(db.String(36), db.ForeignKey('packages.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    is_included = db.Column(db.Boolean, default=True) 

    def __repr__(self):
        return f"<PackageInclusion {self.description}>"

class PackageMedia(BaseModel):
    __tablename__ = "package_media"

    package_id = db.Column(db.String(36), db.ForeignKey("packages.id"))
    image_url = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer)
