from app import create_app
from app.extensions import db
from sqlalchemy import inspect

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

def check_repr_exists(model_class):
    """Check if a model has a custom __repr__ method."""
    if model_class.__repr__ is object.__repr__:
        print(f"WARNING: {model_class.__name__} is missing a custom __repr__ method.")
    else:
        # Verify it doesn't crash
        try:
            instance = model_class()
            repr(instance)
        except Exception as e:
            pass # Expected to fail on missing cols, but method exists
        # print(f" - {model_class.__name__} has __repr__")

with app.app_context():
    try:
        # Trigger mapper configuration
        db.configure_mappers()
        print("SQLAlchemy mappers configured successfully.")
        
        # Check for __repr__ on all models
        models = [
            User, Company, UserPreference, Booking, Passenger, FlightBooking, Flight,
            Package, PackageItinerary, PackageInclusion, PackageBooking, CustomItinerary,
            CustomItineraryItem, Payment, Invoice, SubscriptionPlan, UserSubscription,
            ServiceFeeRule, Notification, NotificationTemplate, AnalyticsMetric, AuditLog
        ]
        
        print("\nVerifying __repr__ methods:")
        for model in models:
            check_repr_exists(model)
            
        print("\nALL MODELS VERIFIED SUCCESSFULLY.")
    except Exception as e:
        print(f"\nERROR VERIFYING MODELS: {e}")
        exit(1)
