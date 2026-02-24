import sys
from app.repository.company.repository import CompanyRepository
from app.repository.booking.repository import BookingRepository

print("Imports successful!")
company_repo = CompanyRepository()
booking_repo = BookingRepository()
print("Instantiations successful!")
