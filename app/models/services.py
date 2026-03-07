from app.models.base import BaseModel
from app.extensions import db

class Service(BaseModel):
    __tablename__ = "services"
    
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(20), nullable=False)
    
    def __repr__(self):
        return f"<Service {self.title}>"