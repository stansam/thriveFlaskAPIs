from flask import Blueprint
from app.extensions import login_manager
from app.models import User
from app.extensions import db

# Import class-based views natively
from app.auth.routes.login import Login
from app.auth.routes.register import Register
from app.auth.routes.verify_email import VerifyEmail
from app.auth.routes.forgot_password import ForgotPassword
from app.auth.routes.reset_password import ResetPassword
from app.auth.routes.logout import Logout
from app.auth.routes.google import GoogleAuthorize, GoogleCallback

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

# --------------------------------------------------------------------------
# Registry Mapper: Explicit unified binding of Endpoints to MethodViews
# --------------------------------------------------------------------------

ROUTES = [
    # Core Account Security
    {"url_rule": "/login", "view_func": Login.as_view("login")},
    {"url_rule": "/register", "view_func": Register.as_view("register")},
    {"url_rule": "/logout", "view_func": Logout.as_view("logout")},
    
    # Verification & Recovery
    {"url_rule": "/verify-email", "view_func": VerifyEmail.as_view("verify_email")},
    {"url_rule": "/forgot-password", "view_func": ForgotPassword.as_view("forgot_password")},
    {"url_rule": "/reset-password", "view_func": ResetPassword.as_view("reset_password")},
    
    # OAuth SSO Flows
    {"url_rule": "/oauth/google", "view_func": GoogleAuthorize.as_view("oauth_google")},
    {"url_rule": "/oauth/callback", "view_func": GoogleCallback.as_view("oauth_callback")},
]

for route in ROUTES:
    auth_bp.add_url_rule(route["url_rule"], view_func=route["view_func"])

__all__ = ["auth_bp"]
