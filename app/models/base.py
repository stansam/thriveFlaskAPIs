import uuid
from datetime import datetime, timedelta, timezone

class BaseModel(db.models):
    __abstract__ = True

    id = db.Column(uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = db.Column(db.Datetime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.Datetime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)