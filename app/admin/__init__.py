from flask import Blueprint

# Explicit view class mapping imports
from app.admin.routes.dashboard import DashboardView
from app.admin.routes.payments import VerifyPaymentView
from app.admin.routes.bookings import UploadTicketView, VoidBookingView
from app.admin.routes.companies import CompanyListView, CompanyStatusView
from app.admin.routes.packages import ManagePackageView
from app.admin.routes.fees import ManageFeesView
from app.admin.routes.audit import AuditLogView

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# --------------------------------------------------------------------------
# Registry Mapper: Explicit unified binding of Endpoints to MethodViews
# --------------------------------------------------------------------------

ROUTES = [
    # Top Level Global Dashboard
    {"url_rule": "/dashboard", "view_func": DashboardView.as_view("global_dashboard")},
    
    # Financial Backoffice Controls
    {"url_rule": "/payments/verify/<booking_id>", "view_func": VerifyPaymentView.as_view("verify_payment")},
    {"url_rule": "/fees", "view_func": ManageFeesView.as_view("manage_fees")},
    
    # Booking & Ticket Issuance Manual Revisions
    {"url_rule": "/bookings/<booking_id>/ticket", "view_func": UploadTicketView.as_view("issue_ticket")},
    {"url_rule": "/bookings/<booking_id>/void", "view_func": VoidBookingView.as_view("void_booking")},
    
    # Corporate (B2B SaaS) Entities Controls
    {"url_rule": "/companies", "view_func": CompanyListView.as_view("list_companies")},
    {"url_rule": "/companies/<company_id>/status", "view_func": CompanyStatusView.as_view("company_status")},
    
    # Holiday Packages Inventory Setup
    {"url_rule": "/packages/manage", "view_func": ManagePackageView.as_view("manage_packages")},
    
    # Compliance ledger mapping
    {"url_rule": "/audit", "view_func": AuditLogView.as_view("audit_logs")}
]

for route in ROUTES:
    admin_bp.add_url_rule(route["url_rule"], view_func=route["view_func"])

__all__ = ["admin_bp"]
