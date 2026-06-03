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
from app.interface.audit import audit_service
from app.interface.loyalty import LoyaltyService
from app.interface.referral import ReferralService
from app.interface.media import MediaService
from app.interface.notification import NotificationService

class _ServiceRegistry:
    """
    Lazily instantiated singleton registry for all Application Domain Services.

    All services are constructed once at import time. Dependencies are injected
    explicitly — services never resolve their own dependencies.
    """
    auth: AuthService = AuthService(
        user_repo=user_repo,
        audit_service=audit_service,
        uow=SQLAlchemyUnitOfWork(),
        denylist=RedisTokenDenylist(),
    )

    user: UserService = UserService(
        user_repo=user_repo,
        user_preference_repo=user_preference_repo,
        audit_service=audit_service,
        uow=SQLAlchemyUnitOfWork(),
    )

    client: ClientService = ClientService(
        client_repo=client_repo,
        client_preference_repo=client_preference_repo,
        booking_repo=booking_repo,
        loyalty_repo=loyalty_repo,
        audit_service=audit_service,
        uow=SQLAlchemyUnitOfWork(),
    ) # log

    corporate: CorporateService = CorporateService(
        corporate_account_repo=corporate_account_repo,
        corporate_subscription_repo=corporate_subscription_repo,
        client_repo=client_repo,
        audit_service=audit_service,
        uow=SQLAlchemyUnitOfWork(),
    ) # log

    fee: FeeService = FeeService(
        fee_schedule_repo=fee_schedule_repo,
        fee_repo=fee_repo,
        fee_snapshot_repo=fee_snapshot_repo,
        audit_service=audit_service,
        uow=SQLAlchemyUnitOfWork(),
    ) # log

    package: PackageService = PackageService(
        package_repo=package_repo,
        package_highlight_repo=package_highlight_repo,
        package_inclusion_repo=package_inclusion_repo,
        package_itinerary_day_repo=package_itinerary_day_repo,
        package_price_tier_repo=package_price_tier_repo,
        package_media_repo=package_media_repo,
        package_booking_repo=package_booking_repo,
        audit_service=audit_service,
        uow=SQLAlchemyUnitOfWork(),
    ) # log

    loyalty: LoyaltyService = LoyaltyService() # log

    referral: ReferralService = ReferralService() # log
    media: MediaService = MediaService()
    notification: NotificationService = NotificationService()


__all__ = [
    "_ServiceRegistry",
]
