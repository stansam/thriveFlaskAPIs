from enum import Enum

class ReferralStatus(str, Enum):
    PENDING   = "pending"    # referee signed up, no booking yet
    QUALIFIED = "qualified"  # referee completed first booking
    CREDITED  = "credited"   # $10 applied to referrer's loyalty ledger
    EXPIRED   = "expired"    # referral window elapsed
