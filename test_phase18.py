from app.services import services

try:
    print("Initializing Service Registry tests...")
    
    auth_srv = services.auth
    user_srv = services.user
    company_srv = services.company
    sub_srv = services.subscription
    flight_srv = services.flight
    pkg_srv = services.package
    pay_srv = services.payment
    notif_srv = services.notification
    analytics_srv = services.analytics
    audit_srv = services.audit
    
    print("All services loaded successfully from the central registry!")
except Exception as e:
    print(f"Failed to load service registry: {e}")
