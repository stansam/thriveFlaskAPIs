from enum import Enum

class BaseEnum(str, Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

class UserRole(BaseEnum):
    CLIENT = "client"
    ADMIN = "admin"
    STAFF = "staff"

class SubscriptionTier(BaseEnum):
    NONE = "none"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"

class BookingStatus(BaseEnum):
    PENDING = "pending"
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    HELD = "held"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"

class BookingType(BaseEnum):
    FLIGHT = "flight"
    PACKAGE = "package"
    HOTEL = "hotel"
    CUSTOM = "custom"

class PaymentStatus(BaseEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"

class PaymentMethod(BaseEnum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MANUAL_TRANSFER = "manual_transfer"
    CREDIT_CARD = "credit_card"

class NotificationType(BaseEnum):
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_REMINDER = "booking_reminder"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    FLIGHT_UPDATE = "flight_update"
    GENERAL = "general"

class TripType(BaseEnum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"
    MULTI_CITY = "multi_city"

class TravelClass(BaseEnum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST_CLASS = "first_class"

class FeeType(BaseEnum):
    FLIGHT_DOMESTIC = "flight_domestic"
    FLIGHT_INTL = "flight_intl"
    URGENT_BOOKING = "urgent_booking"
    GROUP_BOOKING = "group_booking"
    SERVICE_FEE = "service_fee"

class ServiceType(BaseEnum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    ACTIVITY = "activity"
    TRANSPORT = "transport"
