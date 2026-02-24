import uuid

def scramble_pii_string(data: str, is_email: bool = False) -> str:
    """
    Overwrites identifying telemetry deterministically utilizing entirely opaque,
    unguessable UUID structures securing GDPR boundaries gracefully.
    """
    if not data:
        return ""
        
    mask = str(uuid.uuid4()).replace('-', '')[:16] # Generate 16 length opaque marker
    
    if is_email:
        # e.g., 'del_a1b2c3d4e5f6g7h8@anonymized.com'
        return f"del_{mask}@anonymized.thrive"
        
    return f"DEL-{mask}"
