"""
Repository registry.

All repository instances are created once here and imported
throughout the application.  This singleton pattern means:

  1. No per-request instantiation overhead.
  2. A single place to swap repositories for test doubles:
       from repositories import registry
       registry.booking = FakeBookingRepository()

  3. Clean import surface — service layer imports from here:
       from repositories import booking_repo, client_repo

Usage in a Flask service or route:
    from repositories import booking_repo, client_repo, payment_repo

    def confirm_booking(booking_id: str, actor_id: str):
        booking = booking_repo.get_or_404(booking_id)
        booking_repo.transition_status(booking, BookingStatus.CONFIRMED, actor_id)
        db.session.commit()
"""

from .base import BaseRepository, Page

from .user import UserRepository
from .client import ClientRepository
from .corporate import (
    CorporateAccountRepository,
    CorporateSubscriptionRepository,
)
from .package import TravelPackageRepository
from .package_items import (
    PackageHighlightRepository,
    PackageInclusionRepository,
    PackageItineraryDayRepository,
)
from .package_price import PackagePriceTierRepository
from .package_insurance import PackageInsuranceRepository
from .package_media import PackageMediaRepository
from .booking import BookingRepository
from .flight_booking import FlightBookingRepository
from .hotel_booking import HotelBookingRepository
from .car_booking import CarBookingRepository
from .package_booking import PackageBookingRepository
from .booking_passenger import  BookingPassengerRepository

from .payment import PaymentRepository
from .fee import ServiceFeeScheduleRepository, ServiceFeeRepository, ServiceFeeSnapshotRepository
from .referral import ReferralRepository
from .loyalty import LoyaltyLedgerRepository
from .media import MediaAssetRepository
from .notification import NotificationTemplateRepository, NotificationRepository
from .notification_delivery import NotificationDeliveryRepository
from .preference import UserPreferenceRepository, ClientPreferenceRepository
from .audit import AuditLogRepository

class _RepositoryRegistry:
    """
    Lazily instantiated singleton registry.

    Attributes map domain names to repository instances.
    Replace any attribute with a test double before running tests:

        registry.booking = InMemoryBookingRepository()
    """

    # Users & auth
    user:                     UserRepository                   = UserRepository()
    user_preference:          UserPreferenceRepository         = UserPreferenceRepository()

    # Clients & corporate
    client:                   ClientRepository                 = ClientRepository()
    client_preference:        ClientPreferenceRepository       = ClientPreferenceRepository()
    corporate_account:        CorporateAccountRepository       = CorporateAccountRepository()
    corporate_subscription:   CorporateSubscriptionRepository  = CorporateSubscriptionRepository()

    # Packages
    package:                  TravelPackageRepository          = TravelPackageRepository()
    package_highlight:        PackageHighlightRepository       = PackageHighlightRepository()
    package_inclusion:        PackageInclusionRepository       = PackageInclusionRepository()
    package_itinerary_day:    PackageItineraryDayRepository    = PackageItineraryDayRepository()
    package_price_tier:       PackagePriceTierRepository       = PackagePriceTierRepository()
    package_insurance:        PackageInsuranceRepository       = PackageInsuranceRepository()
    package_media:            PackageMediaRepository           = PackageMediaRepository()

    # Bookings
    booking:                  BookingRepository                = BookingRepository()
    flight_booking:           FlightBookingRepository          = FlightBookingRepository()
    hotel_booking:            HotelBookingRepository           = HotelBookingRepository()
    car_booking:              CarBookingRepository             = CarBookingRepository()
    package_booking:          PackageBookingRepository         = PackageBookingRepository()
    booking_passenger:        BookingPassengerRepository       = BookingPassengerRepository()

    # Fees
    fee_schedule:             ServiceFeeScheduleRepository     = ServiceFeeScheduleRepository()
    fee:                      ServiceFeeRepository             = ServiceFeeRepository()
    fee_snapshot:             ServiceFeeSnapshotRepository     = ServiceFeeSnapshotRepository()

    # Payments
    payment:                  PaymentRepository                = PaymentRepository()

    # Referral & loyalty
    referral:                 ReferralRepository               = ReferralRepository()
    loyalty:                  LoyaltyLedgerRepository          = LoyaltyLedgerRepository()

    # Media
    media:                    MediaAssetRepository             = MediaAssetRepository()

    # Notifications
    notification_template:    NotificationTemplateRepository   = NotificationTemplateRepository()
    notification:             NotificationRepository           = NotificationRepository()
    notification_delivery:    NotificationDeliveryRepository   = NotificationDeliveryRepository()

    # Audit
    audit:                    AuditLogRepository               = AuditLogRepository()


# Exported singleton
registry = _RepositoryRegistry()

# Convenience flat aliases — most service files only need 2-3 repos;
# importing the alias saves a `.` lookup each call.
user_repo                  = registry.user
user_preference_repo       = registry.user_preference
client_repo                = registry.client
client_preference_repo     = registry.client_preference
corporate_account_repo     = registry.corporate_account
corporate_subscription_repo = registry.corporate_subscription
package_repo               = registry.package
package_highlight_repo     = registry.package_highlight
package_inclusion_repo     = registry.package_inclusion
package_itinerary_day_repo = registry.package_itinerary_day
package_price_tier_repo    = registry.package_price_tier
package_insurance_repo     = registry.package_insurance
package_media_repo         = registry.package_media
booking_repo               = registry.booking
flight_booking_repo        = registry.flight_booking
hotel_booking_repo         = registry.hotel_booking
car_booking_repo           = registry.car_booking
package_booking_repo       = registry.package_booking
booking_passenger_repo     = registry.booking_passenger
fee_schedule_repo          = registry.fee_schedule
fee_repo                   = registry.fee
fee_snapshot_repo          = registry.fee_snapshot
payment_repo               = registry.payment
referral_repo              = registry.referral
loyalty_repo               = registry.loyalty
media_repo                 = registry.media
notification_template_repo = registry.notification_template
notification_repo          = registry.notification
notification_delivery_repo = registry.notification_delivery
audit_repo                 = registry.audit

__all__ = [
    # Base
    "BaseRepository", "Page",
    # Registry
    "registry",
    # Aliases
    "user_repo", "user_preference_repo",
    "client_repo", "client_preference_repo",
    "corporate_account_repo", "corporate_subscription_repo",
    "package_repo", "package_highlight_repo", "package_inclusion_repo",
    "package_itinerary_day_repo", "package_price_tier_repo", "package_insurance_repo", "package_media_repo",
    "booking_repo", "flight_booking_repo", "hotel_booking_repo",
    "car_booking_repo", "package_booking_repo", "booking_passenger_repo",
    "fee_schedule_repo", "fee_repo", "fee_snapshot_repo",
    "payment_repo",
    "referral_repo", "loyalty_repo",
    "media_repo",
    "notification_template_repo", "notification_repo", "notification_delivery_repo",
    "audit_repo",
]