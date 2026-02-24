from dataclasses import dataclass
from typing import Optional
from app.models.enums import Gender

@dataclass
class UpdateProfileDTO:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    avatar_url: Optional[str] = None
    locale: Optional[str] = None

@dataclass
class UpdatePreferencesDTO:
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    marketing_opt_in: Optional[bool] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
