import secrets
import string

def generate_reference(length: int = 6) -> str:
    """
    Generates a cryptographically strong random alpha-numeric PNR string.
    Useful for creating unique tracking references for Bookings that 
    must resist collision.
    """
    alphabet = string.ascii_uppercase + string.digits
    # Avoid ambiguous characters (I, 1, O, 0) for readability
    safe_chars = ''.join([c for c in alphabet if c not in 'I1O0'])
    return ''.join(secrets.choice(safe_chars) for _ in range(length))
