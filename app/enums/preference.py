from enum import Enum

class ThemePreference(str, Enum):
    LIGHT  = "light"
    DARK   = "dark"
    SYSTEM = "system"


class PreferredChannel(str, Enum):
    """Primary communication channel for a Client."""
    WHATSAPP = "whatsapp"
    EMAIL    = "email"
    SMS      = "sms"
    PHONE    = "phone"


class DocumentFormat(str, Enum):
    """Preferred format for booking confirmations and itineraries."""
    PDF      = "pdf"
    EMAIL    = "email_body" 
    WHATSAPP = "whatsapp_text"


class DashboardLayout(str, Enum):
    """Admin dashboard default view."""
    OVERVIEW    = "overview"
    BOOKINGS    = "bookings"
    CLIENTS     = "clients"
    REVENUE     = "revenue"
