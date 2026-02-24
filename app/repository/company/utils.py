import re

def sanitize_tax_id(tax_id: str) -> str:
    """
    Strips whitespace and non-alphanumeric characters formatting tax numbers 
    consistently for safe DB insertion and lookups.
    """
    if not tax_id:
        return ""
    # Only keep alphanumeric characters (e.g., removing dashes, spaces)
    return re.sub(r'[\W_]+', '', tax_id).upper()
