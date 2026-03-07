from app.models.base import BaseModel
from app.extensions import db
from app.models.enums import OccupancyType

class PackagePricingSeason(BaseModel):
    __tablename__ = "package_pricing_seasons"

    package_id = db.Column(db.String(36), db.ForeignKey("packages.id"))
    name = db.Column(db.String(100))  # High Season 2026
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

class PackagePricing(BaseModel):
    __tablename__ = "package_pricing"

    season_id = db.Column(db.String(36), db.ForeignKey("package_pricing_seasons.id"))
    occupancy_type = db.Column(db.Enum(OccupancyType), nullable=False)  
    adult_price = db.Column(db.Numeric(10,2))
    child_price = db.Column(db.Numeric(10,2))
    infant_price = db.Column(db.Numeric(10,2))