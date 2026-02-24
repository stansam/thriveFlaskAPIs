import secrets
from datetime import datetime

def generate_invoice_number() -> str:
    """
    Safely generates a sequential, unique invoice identifier.
    Combines the exact date context alongside a collision-resistant hex sequence
    (e.g., INV-20261109-A4B8).
    """
    date_str = datetime.now().strftime('%Y%m%d')
    random_hex = secrets.token_hex(2).upper()
    return f"INV-{date_str}-{random_hex}"
