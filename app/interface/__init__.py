"""
Service registry initialization.

Instantiates core services using the pre-existing repository singletons,
a SQLAlchemy-backed Unit of Work, and a Redis-backed token denylist.
"""
from app.repository import (
    user_repo,
    user_preference_repo,
    client_repo,
    client_preference_repo,
    booking_repo,
    loyalty_repo,
    corporate_account_repo,
    corporate_subscription_repo,
    fee_schedule_repo,
    fee_repo,
    fee_snapshot_repo,
    package_repo,
    package_highlight_repo,
    package_inclusion_repo,
    package_itinerary_day_repo,
    package_price_tier_repo,
    package_media_repo,
    package_booking_repo,
)
from app.core.unit_of_work import SQLAlchemyUnitOfWork
from app.core.token_denylist import RedisTokenDenylist
from app.interface.auth import AuthService
from app.interface.user import UserService
from app.interface.client import ClientService
from app.interface.corporate import CorporateService
from app.interface.fee import FeeService
from app.interface.package import PackageService
from app.interface.audit import AuditService
from app.interface.loyalty import LoyaltyService
from app.interface.referral import ReferralService
from app.interface.media import MediaService
from app.interface.notification import NotificationService

class _ServiceRegistry:
    """
    Application service registry.

    Instantiates all domain services once, with explicit dependency injection.
    Must be created inside a Flask application context:
        with app.app_context():
            registry = _ServiceRegistry()
    """
    auth: AuthService
    user: UserService
    client: ClientService
    corporate: CorporateService
    fee: FeeService
    package: PackageService
    loyalty: LoyaltyService
    referral: ReferralService
    media: MediaService
    notification: NotificationService
    audit: AuditService

    def __init__(self) -> None:
        _uow = SQLAlchemyUnitOfWork
        _denylist = RedisTokenDenylist()
        self.audit = AuditService()

        self.auth = AuthService(
            user_repo=user_repo,
            user_preference_repo=user_preference_repo,
            audit_service=self.audit,
            uow=_uow(),
            denylist=_denylist,
        )

        self.user = UserService(
            user_repo=user_repo,
            user_preference_repo=user_preference_repo,
            audit_service=self.audit,
            uow=_uow(),
        )

        self.client = ClientService(
            client_repo=client_repo,
            client_preference_repo=client_preference_repo,
            booking_repo=booking_repo,
            loyalty_repo=loyalty_repo,
            audit_service=self.audit,
            uow=_uow(),
        )

        self.corporate = CorporateService(
            corporate_account_repo=corporate_account_repo,
            corporate_subscription_repo=corporate_subscription_repo,
            client_repo=client_repo,
            audit_service=self.audit,
            uow=_uow(),
        )

        self.fee = FeeService(
            fee_schedule_repo=fee_schedule_repo,
            fee_repo=fee_repo,
            fee_snapshot_repo=fee_snapshot_repo,
            audit_service=self.audit,
            uow=_uow(),
        )

        self.package = PackageService(
            package_repo=package_repo,
            package_highlight_repo=package_highlight_repo,
            package_inclusion_repo=package_inclusion_repo,
            package_itinerary_day_repo=package_itinerary_day_repo,
            package_price_tier_repo=package_price_tier_repo,
            package_media_repo=package_media_repo,
            package_booking_repo=package_booking_repo,
            audit_service=self.audit,
            uow=_uow(),
        )

        self.loyalty = LoyaltyService()
        self.referral = ReferralService()
        self.media = MediaService()
        self.notification = NotificationService()


__all__ = [
    "_ServiceRegistry",
]

