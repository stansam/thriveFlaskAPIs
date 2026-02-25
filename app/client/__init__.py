from flask import Blueprint

# Explicit view class mapping imports
from app.client.routes.profile import ProfileView, PreferencesView, AccountDeletionView
from app.client.routes.booking import UserBookingsView, FlightBookingView, PackageBookingView, BookingPassengersView
from app.client.routes.payment import InvoicePaymentView
from app.client.routes.company import CompanyEmployeesView
from app.client.routes.subscription import SubscriptionUpgradeView

client_bp = Blueprint('client', __name__, url_prefix='/api/client')

# --------------------------------------------------------------------------
# Registry Mapper: Explicit unified binding of Endpoints to MethodViews
# --------------------------------------------------------------------------

ROUTES = [
    # Demographics and Profile Data
    {"url_rule": "/profile", "view_func": ProfileView.as_view("profile")},
    {"url_rule": "/preferences", "view_func": PreferencesView.as_view("preferences")},
    {"url_rule": "/account/delete", "view_func": AccountDeletionView.as_view("account_delete")},
    
    # User Specific Booking Interactions
    {"url_rule": "/bookings", "view_func": UserBookingsView.as_view("user_bookings")},
    {"url_rule": "/flight/book", "view_func": FlightBookingView.as_view("flight_book")},
    {"url_rule": "/package/book", "view_func": PackageBookingView.as_view("package_book")},
    {"url_rule": "/booking/<booking_id>/passengers", "view_func": BookingPassengersView.as_view("booking_passengers")},
    
    # Financial Settle Process
    {"url_rule": "/invoice/<invoice_number>/pay", "view_func": InvoicePaymentView.as_view("invoice_pay")},
    
    # B2B SaaS Logic
    {"url_rule": "/company/employees", "view_func": CompanyEmployeesView.as_view("company_employees")},
    {"url_rule": "/company/employees/<employee_id>", "view_func": CompanyEmployeesView.as_view("company_employee_delete")},
    {"url_rule": "/subscription/upgrade", "view_func": SubscriptionUpgradeView.as_view("subscription_upgrade")},
]

for route in ROUTES:
    client_bp.add_url_rule(route["url_rule"], view_func=route["view_func"])

__all__ = ["client_bp"]
