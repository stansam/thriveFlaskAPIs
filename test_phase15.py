from app.services.flight.service import FlightService
from app.services.package.service import PackageService
from app.dto.flight.schemas import BookFlightDTO, FlightSegmentDTO
from app.dto.package.schemas import BookPackageDTO, SearchPackageDTO
from app.models.enums import TravelClass
from datetime import datetime, date

print("Imports successful!")
svc1 = FlightService()
svc2 = PackageService()

seg1 = FlightSegmentDTO(
    carrier_code="AA", flight_number="123", departure_airport_code="JFK", 
    arrival_airport_code="LHR", departure_time=datetime.now(), arrival_time=datetime.now()
)
dto1 = BookFlightDTO(user_id="123", cabin_class=TravelClass.ECONOMY, segments=[seg1])

dto2 = BookPackageDTO(user_id="123", package_id="456", start_date=date.today(), end_date=date.today())

print("Instantiations successful! DTOs constructed properly.")
