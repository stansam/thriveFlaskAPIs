from enum import Enum


class LoyaltyTransactionType(str, Enum):
    REFERRAL_CREDIT   = "referral_credit"    # earned from a successful referral
    BOOKING_DISCOUNT  = "booking_discount"   # credit redeemed on a booking
    MANUAL_CREDIT     = "manual_credit"      # admin grants credit manually
    MANUAL_DEBIT      = "manual_debit"       # admin corrects an error
    EXPIRY            = "expiry"             # credits expired unused

