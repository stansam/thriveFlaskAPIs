from enum import Enum

class PackageStatus(str, Enum):
    """Lifecycle of a package catalogue entry."""
    DRAFT     = "draft"       # being built by admin
    ACTIVE    = "active"      # live on the website
    PAUSED    = "paused"      # temporarily hidden (e.g. seasonal)
    ARCHIVED  = "archived"    # retired; keep for historical bookings


class InclusionType(str, Enum):
    """
    Maps directly to the business plan notation:
    ✔ INCLUDED, ✘ EXCLUDED, + OPTIONAL (can be added for a fee)
    """
    INCLUDED  = "included"
    EXCLUDED  = "excluded"
    OPTIONAL  = "optional"
