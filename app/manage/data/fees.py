fees = [
    {
        "name": "Domestic Flights",
        "fee_type": "FLIGHT_DOMESTIC",
        "amount_fixed": 25.0, # Range is 25-50, using 25 as base
        "amount_percent": 0.0,
        "priority": 1
    },
    {
        "name": "International Flights",
        "fee_type": "FLIGHT_INTL",
        "amount_fixed": 50.0, # Range is 50-100, using 50 as base
        "amount_percent": 0.0,
        "priority": 1
    },
    {
        "name": "Last-Minute Emergency Booking",
        "fee_type": "URGENT_BOOKING",
        "amount_fixed": 25.0,
        "amount_percent": 0.0,
        "priority": 2
    },
    {
        "name": "Group Bookings",
        "fee_type": "GROUP_BOOKING",
        "amount_fixed": 15.0, # Per traveler (minimum 5)
        "amount_percent": 0.0,
        "priority": 1
    },
]
