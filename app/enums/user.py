from enum import Enum

class UserRole(str, Enum):
    """
    Roles map to feature-level access in the API layer.

    SUPER_ADMIN  — full access, can manage other admins
    ADMIN        — day-to-day operations (Dr. Edna and future staff)
    AGENT        — travel assistant; can create/update bookings but not system config
    READ_ONLY    — reporting / accounting integrations
    """
    SUPER_ADMIN = "super_admin"
    ADMIN       = "admin"
    AGENT       = "agent"
    READ_ONLY   = "read_only"