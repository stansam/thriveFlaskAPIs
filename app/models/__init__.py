# models/__init__.py
from .base import db, AuditMixin
from .user import User
from .client import Client
from .corporate import CorporateAccount, CorporateSubscription
from .media import MediaAsset
from .package_media import PackageMedia
from .user_preference import UserPreference
from .client_preference import ClientPreference
from .notification import Notification
from .notification_delivery import NotificationDelivery
from .notification_template import NotificationTemplate
from .package import TravelPackage
from .package_items import PackageHighlight, PackageInclusion, PackageItineraryDay
from .package_price_tier import PackagePriceTier
from .booking import Booking
from .booking_passenger import  BookingPassenger
from .flight_booking import FlightBooking, FlightSegment
from .hotel_booking import HotelBooking 
from .car_booking import CarBooking 
from .package_booking import PackageBooking
from .fee import ServiceFee
from .fee_schedule import ServiceFeeSchedule
from .fee_snapshot import ServiceFeeSnapshot 
from .payment import Payment
from .referral import Referral
from .loyalty import LoyaltyLedger
from .audit import AuditLog

__all__ = [
    "db", "AuditMixin",
    "User",
    "Client",
    "CorporateAccount",
    "CorporateSubscription",
    "MediaAsset",
    "PackageMedia",
    "UserPreference",
    "ClientPreference",
    "Notification",
    "NotificationDelivery",
    "NotificationTemplate",
    "TravelPackage",
    "PackageHighlight", "PackageInclusion", "PackageItineraryDay",
    "PackagePriceTier",
    "Booking",
    "BookingPassenger",
    "FlightBooking", "FlightSegment",
    "HotelBooking",
    "CarBooking",
    "PackageBooking",
    "ServiceFee",
    "ServiceFeeSchedule",
    "ServiceFeeSnapshot",
    "Payment",
    "Referral",
    "LoyaltyLedger",
    "AuditLog",
]
