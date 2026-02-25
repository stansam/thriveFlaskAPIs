from typing import List, Optional
from datetime import datetime
from app.models.package import Package
from app.models.package_booking import PackageBooking, CustomItinerary, CustomItineraryItem
from app.models.enums import BookingStatus, ServiceType
from app.repository import repositories
from app.dto.package.schemas import SearchPackageDTO, BookPackageDTO
from app.services.package.utils import build_package_search_filters, validate_package_duration

class PackageService:
    """
    PackageService manages pre-configured holiday logic explicitly bounding dates,
    capacities, and generating customized itinerary permutations underneath a Booking.
    """

    def __init__(self):
        self.package_repo = repositories.package
        self.package_booking_repo = repositories.package_booking
        self.booking_repo = repositories.booking
        self.user_repo = repositories.user

    def search_packages(self, filters: SearchPackageDTO) -> List[Package]:
        """
        Dynamically constructs SQLAlchemy filter rules trapping duration windows
        and geographical nodes returning active packages natively.
        """
        # Convert DTO attributes dynamically
        filters_dict = getattr(filters, "model_dump", lambda: getattr(filters, "dict", lambda: vars(filters))())()
        return self.package_repo.search_packages(filters=filters_dict)

    def book_package(self, data: BookPackageDTO) -> PackageBooking:
        """
        Executes a transactional block:
        1. Validates the User entitlements.
        2. Validates the physical duration exactly aligns with the Package definition.
        3. Creates the overarching Booking mapping.
        4. Links the PackageBooking payload holding traveler metrics securely.
        """
        user = self.user_repo.get_by_id(data.user_id)
        if not user or not user.can_book():
            raise PermissionError("User lacks active booking entitlements or has exhausted their tier limit.")
            
        package = self.package_repo.get_by_id(data.package_id)
        if not package or not package.is_active:
             raise ValueError("Target package is currently unavailable.")
             
        # Strict validation ensuring users don't book a 3-day window for a 10-day package
        validate_package_duration(data.start_date, data.end_date, package.duration_days)

        try:
            # 1. Base Booking
            booking_core = self.booking_repo.create({
                "user_id": user.id,
                "status": BookingStatus.PENDING,
                "company_id": user.company_id 
            }, commit=False)

            # 2. PackageBooking Context
            package_booking = self.package_booking_repo.create({
                "booking_id": booking_core.id,
                "package_id": package.id,
                "start_date": data.start_date,
                "end_date": data.end_date,
                "number_of_adults": data.number_of_adults,
                "number_of_children": data.number_of_children,
                "special_requests": data.special_requests
            }, commit=True)
            return package_booking

        except Exception as e:
            raise RuntimeError(f"Package booking transaction failed cleanly: {str(e)}")

    def customize_itinerary(self, package_booking_id: str, title: str, items: list) -> CustomItinerary:
        """
        Securely appends bespoke itinerary deviations explicitly onto a finished 
        `PackageBooking` node generating physical overrides.
        """
        package_booking = self.package_booking_repo.get_by_id(package_booking_id)
        if not package_booking:
            raise ValueError("Invalid package booking target.")

        return self.package_booking_repo.override_custom_itinerary(
            package_booking=package_booking,
            title=title,
            items=items
        )
