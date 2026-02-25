from typing import Optional
from app.models.company import Company
from app.models.user import User
from app.models.enums import UserRole
from app.repository import repositories
from app.dto.company.schemas import OnboardCompanyDTO, ManageEmployeeDTO
from app.services.company.utils import enforce_employee_limits
from app.services.auth.service import AuthService
from app.dto.auth.schemas import RegisterRequestDTO

class CompanyService:
    """
    CompanyService drives enterprise B2B registrations dynamically coupling the entity
    alongside a founding Admin user recursively enforcing employee hierarchy limits.
    """

    def __init__(self):
        self.company_repo = repositories.company
        self.user_repo = repositories.user
        self.auth_service = AuthService()

    def onboard_company(self, data: OnboardCompanyDTO) -> Company:
        """
        Registers the corporate entity and inherently bootstraps the overarching Admin account 
        in a unified workflow mapping the `company_id` natively backwards.
        """
        # 1. Create the overarching Entity cleanly
        company = self.company_repo.create({
            "name": data.name,
            "tax_id": data.tax_id,
            "address": data.address,
            "contact_email": data.contact_email
        }, commit=True)
        
        # 2. Re-route the employee creation safely through the AuthService to gain password hashing and DB persistence natively
        admin_payload = RegisterRequestDTO(
            first_name=data.admin_user.first_name,
            last_name=data.admin_user.last_name,
            email=data.admin_user.email,
            password=data.admin_user.password,
            phone=data.admin_user.phone,
            role=UserRole.ADMIN,
            company_id=company.id
        )
        
        try:
            self.auth_service.register_user(admin_payload)
        except Exception as e:
            # Rollback the company entirely if the Admin setup failed (e.g., duplicated email)
            self.company_repo.delete(company.id)
            raise ValueError(f"Company creation failed during admin initialization: {str(e)}")

        return company

    def manage_employees(self, company_id: str, admin_id: str, payload: ManageEmployeeDTO, target_user_id: Optional[str] = None) -> Optional[User]:
        """
        Provides CRUD execution pathways for a given company's internal manifest
        strictly mapping changes against underlying enterprise subscription limits.
        """
        admin = self.user_repo.get_by_id(admin_id)
        if not admin or admin.company_id != company_id or admin.role != UserRole.ADMIN:
            raise PermissionError("Only active company Administrators can manage the employee manifest.")
            
        company = self.company_repo.get_by_id(company_id)
        if not company:
            raise ValueError("Invalid corporate entity.")

        # ACTION: ADD
        if payload.action == 'add' and payload.user_data:
            enforce_employee_limits(company)
            # Route new seats natively through Auth ensuring passwords hash correctly
            employee_dto = RegisterRequestDTO(
                first_name=payload.user_data.first_name,
                last_name=payload.user_data.last_name,
                email=payload.user_data.email,
                password=payload.user_data.password,
                phone=payload.user_data.phone,
                role=UserRole.CLIENT,
                company_id=company.id
            )
            return self.auth_service.register_user(employee_dto)
            
        # ACTION: REMOVE
        if payload.action == 'remove' and target_user_id:
            target = self.user_repo.get_by_id(target_user_id)
            if target and target.company_id == company.id:
                # Soft sever the B2B linkage entirely rather than deleting the user's booking history
                return self.user_repo.update(target.id, {"company_id": None}, commit=True)
            return None
            
        # ACTION: UPDATE
        if payload.action == 'update' and payload.user_data and target_user_id:
             target = self.user_repo.get_by_id(target_user_id)
             if target and target.company_id == company.id:
                 update_dict = {
                     "first_name": payload.user_data.first_name,
                     "last_name": payload.user_data.last_name,
                     "phone": payload.user_data.phone
                 }
                 return self.user_repo.update(target.id, update_dict, commit=True)
                 
        raise ValueError("Invalid management action combination passed to employee processor.")
