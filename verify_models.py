from app import create_app
from app.extensions import db

# Import all models to ensure they are registered
from app.models.base import BaseModel
from app.models.user import User
from app.models.company import Company
from app.models.user_preference import UserPreference
from app.models.booking import Booking
from app.models.passenger import Passenger
from app.models.flight_booking import FlightBooking, Flight
from app.models.package import Package, PackageItinerary, PackageInclusion
from app.models.package_booking import PackageBooking, CustomItinerary, CustomItineraryItem
from app.models.payment import Payment, Invoice, SubscriptionPlan, UserSubscription
from app.models.service_fee import ServiceFeeRule
from app.models.notification import Notification, NotificationTemplate
from app.models.analytics import AnalyticsMetric
from app.models.audit_log import AuditLog

app = create_app()

with app.app_context():
    try:
        # This will trigger mapper configuration and catch many common errors
        db.configure_mappers()
        print("SQLAlchemy mappers configured successfully.")
        
        # Optional: Print all registered tables
        print("Registered Tables:")
        for table in db.metadata.sorted_tables:
            print(f" - {table.name}")
            
        print("\nALL MODELS VERIFIED SUCCESSFULLY.")
    except Exception as e:
        print(f"\nERROR VERIFYING MODELS: {e}")
        exit(1)
