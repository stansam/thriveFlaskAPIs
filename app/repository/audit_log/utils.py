import copy

# Hardcoded keys representing extremely sensitive data values never to be written to raw logs
SENSITIVE_KEYS = {
    'password', 'password_hash', 'credit_card', 'cvv', 
    'card_number', 'ssn', 'secret', 'token', 'authorization'
}

def sanitize_audit_payload(changes: dict) -> dict:
    """
    Recursively clones and strips explicit sensitive information 
    from a JSON payload before it hits the immutable PostgreSQL Audit ledger.
    """
    if not changes:
        return {}
        
    safe_copy = copy.deepcopy(changes)
    
    def _scrub(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k).lower() in SENSITIVE_KEYS:
                    obj[k] = '[REDACTED]'
                else:
                    obj[k] = _scrub(v)
        elif isinstance(obj, list):
            obj = [_scrub(item) for item in obj]
        return obj

    return _scrub(safe_copy)
