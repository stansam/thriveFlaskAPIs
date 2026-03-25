from enum import Enum 

class BookingStatus(str, Enum):
    """
    Full lifecycle of a booking request.

    PENDING_PAYMENT  — client has submitted request; awaiting manual payment
    PAYMENT_RECEIVED — admin has confirmed receipt of funds
    CONFIRMED        — ticket / reservation issued; sent to client
    ON_HOLD          — waiting for airline / hotel hold to be confirmed
    CANCELLED        — cancelled (by client or admin)
    REFUNDED         — payment returned (partial or full)
    COMPLETED        — travel has occurred; booking closed
    """
    PENDING_PAYMENT  = "pending_payment"
    PAYMENT_RECEIVED = "payment_received"
    CONFIRMED        = "confirmed"
    ON_HOLD          = "on_hold"
    CANCELLED        = "cancelled"
    REFUNDED         = "refunded"
    COMPLETED        = "completed"


class BookingServiceType(str, Enum):
    FLIGHT  = "flight"
    HOTEL   = "hotel"
    CAR     = "car"
    PACKAGE = "package"


class FlightCabin(str, Enum):
    ECONOMY        = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS       = "business"
    FIRST          = "first"


class RoomType(str, Enum):
    STANDARD = "standard"
    DELUXE   = "deluxe"
    SUITE    = "suite"
    TWIN     = "twin"
    FAMILY   = "family"


class CarCategory(str, Enum):
    ECONOMY    = "economy"
    COMPACT    = "compact"
    MID_SIZE   = "mid_size"
    FULL_SIZE  = "full_size"
    SUV        = "suv"
    LUXURY     = "luxury"
    VAN        = "van"
