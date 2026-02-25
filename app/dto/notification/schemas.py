from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DispatchNotificationDTO:
    user_id: str
    trigger_event: str
    context: Dict[str, Any]

@dataclass
class SendEmailDTO:
    to_email: str
    subject: str
    body_html: str
