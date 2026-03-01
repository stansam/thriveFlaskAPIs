def validate_service_payload(service: dict) -> dict:
    """
    Sanitizes raw external dict payloads checking keys and standardizing string representations
    for core fields like passport numbers before they hit the Bulk Insert engine.
    """
    if 'title' in service and service['title']:
        service['title'] = str(service['title']).strip().upper()
    if 'icon' in service and service['icon']:
        service['icon'] = str(service['icon']).strip().upper()
        
    if 'description' in service and isinstance(service['description'], str):
        service['description'] = str(service['description']).strip().upper()
             
    return service