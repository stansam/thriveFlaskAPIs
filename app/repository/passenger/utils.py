from datetime import datetime

def validate_passenger_payload(passenger: dict) -> dict:
    """
    Sanitizes raw external dict payloads checking keys and standardizing string representations
    for core fields like passport numbers before they hit the Bulk Insert engine.
    """
    if 'passport_number' in passenger and passenger['passport_number']:
        passenger['passport_number'] = str(passenger['passport_number']).strip().upper()
        
    if 'date_of_birth' in passenger and isinstance(passenger['date_of_birth'], str):
        # Ensure it casts properly to Date types across SQL Dialects
        try:
             # Basic ISO format check fallback if JSON didn't automatically parse it
             datetime.strptime(passenger['date_of_birth'], '%Y-%m-%d')
        except ValueError:
             pass # Let the DB driver handle or reject it natively for now
             
    return passenger
