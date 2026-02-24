from dataclasses import dataclass
from typing import Optional
from app.models.enums import UserRole, Gender

@dataclass
class LoginRequestDTO:
    email: str
    password: str
    remember: bool = False

@dataclass
class RegisterRequestDTO:
    first_name: str
    last_name: str
    email: str
    password: str
    phone: Optional[str] = None
    role: UserRole = UserRole.CLIENT
    gender: Optional[Gender] = None
    locale: Optional[str] = None
    company_id: Optional[str] = None
