from enum import Enum


class ClientType(str, Enum):
    INDIVIDUAL = "individual"
    CORPORATE  = "corporate"
    GROUP      = "group"
    EMERGENCY  = "emergency"

class SubscriptionTier(str, Enum):
    """
    Mirrors the business plan pricing matrix.
    Bronze  — $150/month, up to 6 bookings
    Silver  — $300/month, up to 15 bookings
    Gold    — $500/month, unlimited bookings + 24/7 concierge
    """
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD   = "gold"

