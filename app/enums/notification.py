from enum import Enum

class NotificationEventType(str, Enum):
    """
    All system events that can trigger a notification.
    Maps 1:1 to service-layer event names.
    """
    # Booking lifecycle
    BOOKING_CREATED           = "booking_created"
    BOOKING_CONFIRMED         = "booking_confirmed"
    BOOKING_CANCELLED         = "booking_cancelled"
    BOOKING_COMPLETED         = "booking_completed"
    BOOKING_ON_HOLD           = "booking_on_hold"
    BOOKING_REMINDER_PRE_TRIP = "booking_reminder_pre_trip"    # 48h before departure
    BOOKING_REMINDER_BALANCE  = "booking_reminder_balance"     # outstanding balance

    # Payment
    PAYMENT_RECEIVED          = "payment_received"
    PAYMENT_FAILED            = "payment_failed"
    PAYMENT_REFUNDED          = "payment_refunded"

    # Client
    CLIENT_WELCOME            = "client_welcome"               # new client onboarded
    CLIENT_REFERRAL_QUALIFIED = "client_referral_qualified"    # referral credited

    # Corporate
    SUBSCRIPTION_RENEWED      = "subscription_renewed"
    SUBSCRIPTION_EXPIRING     = "subscription_expiring"        # 7-day warning
    SUBSCRIPTION_LIMIT_WARNING = "subscription_limit_warning"  # 80% of booking cap

    # Package
    PACKAGE_PUBLISHED         = "package_published"            # new package live
    PACKAGE_DEAL_ALERT        = "package_deal_alert"           # marketing broadcast

    # Auth
    USER_PASSWORD_RESET       = "user_password_reset"
    USER_LOGIN_NEW_DEVICE     = "user_login_new_device"
    USER_CREATED              = "user_created"

    # Admin
    ADMIN_BOOKING_ASSIGNED    = "admin_booking_assigned"
    ADMIN_EXPORT_READY        = "admin_export_ready"


class NotificationChannel(str, Enum):
    """Delivery channels ordered by typical preference."""
    IN_APP   = "in_app"
    EMAIL    = "email"
    WHATSAPP = "whatsapp"
    SMS      = "sms"
    PUSH     = "push"        # future: mobile app push notifications


class NotificationPriority(str, Enum):
    LOW    = "low"
    NORMAL = "normal"
    HIGH   = "high"
    URGENT = "urgent"    # payment failures, security events


class NotificationStatus(str, Enum):
    """Overall status of the Notification (across all delivery channels)."""
    PENDING   = "pending"    # queued; no delivery attempted yet
    SENDING   = "sending"    # at least one channel in-flight
    DELIVERED = "delivered"  # delivered on at least one channel
    FAILED    = "failed"     # all delivery attempts exhausted
    READ      = "read"       # recipient has opened the notification
    DISMISSED = "dismissed"  # recipient explicitly dismissed it


class DeliveryStatus(str, Enum):
    """Status of one NotificationDelivery attempt."""
    QUEUED    = "queued"
    SENT      = "sent"
    DELIVERED = "delivered"
    OPENED    = "opened"     # email open / WhatsApp read receipt
    FAILED    = "failed"
    BOUNCED   = "bounced"    # email hard bounce
    RETRYING  = "retrying"


class RecipientType(str, Enum):
    USER   = "user"
    CLIENT = "client"
    ADMIN = "admin"