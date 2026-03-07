companies = [
    {
        "name": "Acme Corp Travel",
        "tax_id": "TAX-123456",
        "address": "123 Business Rd, New York, NY",
        "contact_email": "travel@acmecorp.com"
    }
]

users = [
    {
        "first_name": "John",
        "last_name": "Client",
        "email": "john.client@example.com",
        "password": "Password123!",
        "phone": "+1234567890",
        "role": "CLIENT",
        "gender": "MALE",
        "preferences": {
            "currency": "USD",
            "language": "en",
            "timezone": "UTC",
            "marketing_opt_in": True,
            "email_updates": True
        }
    },
    {
        "first_name": "Jane",
        "last_name": "Corporate",
        "email": "jane@acmecorp.com",
        "password": "Password123!",
        "phone": "+1987654321",
        "role": "CLIENT",
        "gender": "FEMALE",
        "company_index": 0, # Index of the company in the companies list
        "preferences": {
            "currency": "USD",
            "language": "en",
            "timezone": "EST",
            "marketing_opt_in": False,
            "email_updates": True
        }
    },
    {
        "first_name": "Mark",
        "last_name": "Staff",
        "email": "mark.staff@thrivetravel.com",
        "password": "Password123!",
        "phone": "+1122334455",
        "role": "STAFF",
        "gender": "MALE",
        "preferences": {
            "currency": "USD",
            "language": "en",
            "timezone": "UTC",
            "marketing_opt_in": False,
            "email_updates": False
        }
    }
]
