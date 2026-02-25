from app.services.company.service import CompanyService
from app.services.subscription.service import SubscriptionService
from app.dto.company.schemas import OnboardCompanyDTO, EmployeeDTO
from app.dto.subscription.schemas import SubscribeToPlanDTO

print("Imports successful!")
svc1 = CompanyService()
svc2 = SubscriptionService()

dto1 = EmployeeDTO(first_name="Admin", last_name="User", email="admin@corp.com", password="pwd")
dto2 = OnboardCompanyDTO(name="Acme Corp", admin_user=dto1)

print("Instantiations successful! DTOs constructed properly.")
