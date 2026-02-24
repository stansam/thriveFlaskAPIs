def normalize_email(email: str) -> str:
    """Provides consistent lowercase normalization for DB comparison and insertion."""
    if not email:
        return ""
    return email.strip().lower()
