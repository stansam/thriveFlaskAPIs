from app.repository.user.repository import UserRepository
from app.repository.company.repository import CompanyRepository
from app.repository.subscription.repository import SubscriptionRepository
from app.repository.booking.repository import BookingRepository
from app.repository.flight_booking.repository import FlightBookingRepository
from app.repository.package.repository import PackageRepository
from app.repository.package_departure.repository import PackageDepartureRepository
from app.repository.package_booking.repository import PackageBookingRepository
from app.repository.invoice.repository import InvoiceRepository
from app.repository.payment.repository import PaymentRepository
from app.repository.passenger.repository import PassengerRepository
from app.repository.service_fee.repository import ServiceFeeRepository
from app.repository.audit_log.repository import AuditLogRepository
from app.repository.notification.repository import NotificationRepository
from app.repository.analytics.repository import AnalyticsRepository


class RepositoryRegistry:
    """
    Centralized Singleton factory mapping all repository workflows lazily. 
    Prevents redundant instantiations across the Service layer globally.
    """
    def __init__(self):
        self._user = None
        self._company = None
        self._subscription = None
        self._booking = None
        self._flight_booking = None
        self._package = None
        self._package_departure = None
        self._package_booking = None
        self._invoice = None
        self._payment = None
        self._passenger = None
        self._service_fee = None
        self._audit_log = None
        self._notification = None
        self._analytics = None

    @property
    def user(self) -> UserRepository:
        if not self._user:
            self._user = UserRepository()
        return self._user

    @property
    def company(self) -> CompanyRepository:
        if not self._company:
            self._company = CompanyRepository()
        return self._company
        
    @property
    def subscription(self) -> SubscriptionRepository:
        if not self._subscription:
            self._subscription = SubscriptionRepository()
        return self._subscription

    @property
    def booking(self) -> BookingRepository:
        if not self._booking:
            self._booking = BookingRepository()
        return self._booking

    @property
    def flight_booking(self) -> FlightBookingRepository:
        if not self._flight_booking:
            self._flight_booking = FlightBookingRepository()
        return self._flight_booking

    @property
    def package(self) -> PackageRepository:
        if not self._package:
            self._package = PackageRepository()
        return self._package

    @property
    def package_departure(self) -> PackageDepartureRepository:
        if not self._package_departure:
            self._package_departure = PackageDepartureRepository()
        return self._package_departure

    @property
    def package_booking(self) -> PackageBookingRepository:
        if not self._package_booking:
            self._package_booking = PackageBookingRepository()
        return self._package_booking

    @property
    def invoice(self) -> InvoiceRepository:
        if not self._invoice:
            self._invoice = InvoiceRepository()
        return self._invoice

    @property
    def payment(self) -> PaymentRepository:
        if not self._payment:
            self._payment = PaymentRepository()
        return self._payment

    @property
    def passenger(self) -> PassengerRepository:
        if not self._passenger:
            self._passenger = PassengerRepository()
        return self._passenger

    @property
    def service_fee(self) -> ServiceFeeRepository:
        if not self._service_fee:
            self._service_fee = ServiceFeeRepository()
        return self._service_fee

    @property
    def audit_log(self) -> AuditLogRepository:
        if not self._audit_log:
            self._audit_log = AuditLogRepository()
        return self._audit_log

    @property
    def notification(self) -> NotificationRepository:
        if not self._notification:
            self._notification = NotificationRepository()
        return self._notification

    @property
    def analytics(self) -> AnalyticsRepository:
        if not self._analytics:
            self._analytics = AnalyticsRepository()
        return self._analytics

# Global singleton instance for the entire app to securely import
repositories = RepositoryRegistry()
