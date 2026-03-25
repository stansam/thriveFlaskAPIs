from enum import Enum


class FeeType(str, Enum):
    """
    Maps to each line in the pricing schedule.
    """
    DOMESTIC_FLIGHT       = "domestic_flight"
    INTERNATIONAL_FLIGHT  = "international_flight"
    EMERGENCY_SURCHARGE   = "emergency_surcharge"
    GROUP_PER_PAX         = "group_per_pax"
    HOTEL                 = "hotel"
    CAR_RENTAL            = "car_rental"
    ITINERARY_BASIC       = "itinerary_basic"
    ITINERARY_PREMIUM     = "itinerary_premium"
    VISA_CONSULTATION     = "visa_consultation"
    TRAVEL_INSURANCE_COMM = "travel_insurance_commission"   # percentage-based


class BookingChannel(str, Enum):
    """
    Channel through which the booking was initiated.
    Useful for analytics; may affect fee in future.
    """
    WEB       = "web"
    WHATSAPP  = "whatsapp"
    EMAIL     = "email"
    PHONE     = "phone"
    WALK_IN   = "walk_in"
