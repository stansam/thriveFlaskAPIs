from dataclasses import dataclass
from typing import Optional

@dataclass
class EmployeeDTO:
    first_name: str
    last_name: str
    email: str
    password: str
    phone: Optional[str] = None

@dataclass
class OnboardCompanyDTO:
    name: str
    admin_user: EmployeeDTO
    tax_id: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[str] = None

@dataclass
class ManageEmployeeDTO:
    action: str # Requires 'add', 'remove', or 'update'
    user_data: Optional[EmployeeDTO] = None
