from datetime import datetime, timezone
import uuid
from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import AuditAction, EntityType

class AuditLog(BaseModel):
    __tablename__ = 'audit_logs'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)
    action = db.Column(db.Enum(AuditAction), nullable=False)
    entity_type = db.Column(db.Enum(EntityType))
    entity_id = db.Column(db.String(36))
    description = db.Column(db.Text)
    changes = db.Column(db.JSON)  
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id} by {self.user_id}>"
