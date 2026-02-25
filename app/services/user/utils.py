import hashlib

def scramble_pii_string(data: str, is_email: bool = False) -> str:
    """
    Overwrites identifying telemetry deterministically utilizing entirely opaque,
    cryptographically secure hashes securing GDPR boundaries gracefully.
    """
    if not data:
        return ""
        
    salt = b"thrive_gdpr_salt_"
    mask = hashlib.sha256(salt + data.encode('utf-8')).hexdigest()[:16]
    
    if is_email:
        # e.g., 'del_a1b2c3d4e5f6g7h8@anonymized.thrive'
        return f"del_{mask}@anonymized.thrive"
        
    return f"DEL-{mask}"
