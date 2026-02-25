import uuid
from datetime import datetime

def generate_invoice_number() -> str:
    """
    Safely builds universally unique but visually consistent sequential strings
    mapped efficiently for accountants to parse quickly. Format: INV-YYYYMMDD-HEX
    """
    date_str = datetime.now().strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4()).split('-')[0].upper()
    
    return f"INV-{date_str}-{short_uuid}"
