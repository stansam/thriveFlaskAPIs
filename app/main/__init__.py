from flask import Blueprint

# Explicit view class mapping imports
from app.main.routes.flights import FlightSearchView
from app.main.routes.packages import PackageListView, PackageDetailView, FeaturedPackageListView
from app.main.routes.departures import DepartureListView
from app.main.routes.pricing import PricingTierView
from app.main.routes.contact import ContactView

# Per User instruction URL prefix should strictly be `/api` here explicitly decoupling Auth and Client boundaries natively.
main_bp = Blueprint('main', __name__, url_prefix='/api')

# --------------------------------------------------------------------------
# Registry Mapper: Explicit unified binding of Endpoints to MethodViews
# --------------------------------------------------------------------------

ROUTES = [
    # Top Level Operations
    {"url_rule": "/flights/search", "view_func": FlightSearchView.as_view("flight_search")},
    
    # Packages and Bookings Discovery Catalog
    {"url_rule": "/packages", "view_func": PackageListView.as_view("package_list")},
    {"url_rule": "/packages/featured", "view_func": FeaturedPackageListView.as_view("featured_package_list")},
    {"url_rule": "/packages/<slug>", "view_func": PackageDetailView.as_view("package_detail")},
    {"url_rule": "/departures", "view_func": DepartureListView.as_view("departure_slots")},
    
    # Global System & Contact info
    {"url_rule": "/pricing-tiers", "view_func": PricingTierView.as_view("pricing_tiers")},
    {"url_rule": "/contact", "view_func": ContactView.as_view("contact_inquiry")}
]

for route in ROUTES:
    main_bp.add_url_rule(route["url_rule"], view_func=route["view_func"])

__all__ = ["main_bp"]
