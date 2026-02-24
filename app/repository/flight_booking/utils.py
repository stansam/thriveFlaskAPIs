def normalize_pnr(pnr: str) -> str:
    """
    Strips whitespace and normalizes case. Airlines expect specific length combinations, 
    but strictly resolving them to uppercase enables safer DB evaluations.
    """
    if not pnr:
        return ""
    return pnr.strip().upper()
