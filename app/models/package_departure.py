from app.models.base import BaseModel
from app.models.enums import PackageDepartureStatus
from app.extensions import db

class PackageDeparture(BaseModel):
    __tablename__ = "package_departures"

    package_id = db.Column(db.String(36), db.ForeignKey("packages.id"))

    departure_date = db.Column(db.Date, index=True)
    return_date = db.Column(db.Date)

    total_capacity = db.Column(db.Integer)
    available_capacity = db.Column(db.Integer)

    status = db.Column(db.Enum(PackageDepartureStatus), default=PackageDepartureStatus.OPEN)