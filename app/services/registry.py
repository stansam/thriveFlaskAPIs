from app.services.auth.service import AuthService
from app.services.user.service import UserService
from app.services.company.service import CompanyService
from app.services.subscription.service import SubscriptionService
from app.services.flight.service import FlightService
from app.services.package.service import PackageService
from app.services.payment.service import PaymentService
from app.services.notification.service import NotificationService
from app.services.analytics.service import AnalyticsService
from app.services.audit.service import AuditService


class ServiceRegistry:
    """
    Centralized Singleton factory mapping all service workflows lazily.
    Prevents redundant instantiations across controllers or endpoints globally.
    """
    def __init__(self):
        self._auth = None
        self._user = None
        self._company = None
        self._subscription = None
        self._flight = None
        self._package = None
        self._payment = None
        self._notification = None
        self._analytics = None
        self._audit = None

    @property
    def auth(self) -> AuthService:
        if not self._auth:
            self._auth = AuthService()
        return self._auth

    @property
    def user(self) -> UserService:
        if not self._user:
            self._user = UserService()
        return self._user

    @property
    def company(self) -> CompanyService:
        if not self._company:
            self._company = CompanyService()
        return self._company

    @property
    def subscription(self) -> SubscriptionService:
        if not self._subscription:
            self._subscription = SubscriptionService()
        return self._subscription

    @property
    def flight(self) -> FlightService:
        if not self._flight:
            self._flight = FlightService()
        return self._flight

    @property
    def package(self) -> PackageService:
        if not self._package:
            self._package = PackageService()
        return self._package

    @property
    def payment(self) -> PaymentService:
        if not self._payment:
            self._payment = PaymentService()
        return self._payment

    @property
    def notification(self) -> NotificationService:
        if not self._notification:
            self._notification = NotificationService()
        return self._notification

    @property
    def analytics(self) -> AnalyticsService:
        if not self._analytics:
            self._analytics = AnalyticsService()
        return self._analytics

    @property
    def audit(self) -> AuditService:
        if not self._audit:
             self._audit = AuditService()
        return self._audit


# Global singleton instance for the entire app endpoints to seamlessly import
services = ServiceRegistry()
