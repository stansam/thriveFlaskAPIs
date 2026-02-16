from app.extensions import db
from app.models.base import BaseModel
from app.models.enums import NotificationType, NotificationPriority

class Notification(BaseModel):
    __tablename__ = "notifications"
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    type = db.Column(db.Enum(NotificationType), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    is_read = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(255))
    
    priority = db.Column(db.Enum(NotificationPriority), default=NotificationPriority.NORMAL) 

    def __repr__(self):
        return f"<Notification {self.id} - {self.type} ({self.priority})>"


class NotificationTemplate(BaseModel):
    __tablename__ = "notification_templates"
    
    trigger_event = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    subject_template = db.Column(db.String(255))
    body_html_template = db.Column(db.Text)
    sms_template = db.Column(db.String(160))
    
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<NotificationTemplate {self.name} ({self.trigger_event})>"