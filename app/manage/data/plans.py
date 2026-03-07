plans = [
    {
        "name": "Bronze",
        "tier": "BRONZE",
        "price_monthly": 150.0,
        "currency": "USD",
        "booking_limit_count": 6,
        "fee_waiver_rules": {}
    },
    {
        "name": "Silver",
        "tier": "SILVER",
        "price_monthly": 300.0,
        "currency": "USD",
        "booking_limit_count": 15,
        "fee_waiver_rules": {}
    },
    {
        "name": "Gold",
        "tier": "GOLD",
        "price_monthly": 500.0,
        "currency": "USD",
        "booking_limit_count": -1, # Using -1 or a very high number for unlimited
        "fee_waiver_rules": {"concierge": "24/7"}
    }
]
