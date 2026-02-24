from app.services.auth.service import AuthService
from app.services.user.service import UserService
from app.dto.auth.schemas import LoginRequestDTO
from app.dto.user.schemas import UpdateProfileDTO

print("Imports successful!")
svc1 = AuthService()
svc2 = UserService()
dto1 = LoginRequestDTO(email="test@test.com", password="pwd")
dto2 = UpdateProfileDTO(first_name="Test")
print("Instantiations successful!")
