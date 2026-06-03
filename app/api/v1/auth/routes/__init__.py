# app/api/v1/auth/routes/__init__.py
"""
Auth blueprint route registrations.
"""
from app.api.v1.auth.routes.routes import (
    LoginView,
    LogoutView,
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView,
    MFAEnrollView,
    MFAConfirmView,
    MFADisableView,
    RegisterView,
    GoogleLoginView,
    GoogleCallbackView,
)
from app.api.v1.utils import RouteConfig

AUTH_ROUTES: list[RouteConfig] = [
    {
        "url_rule": "/login",
        "view_func": LoginView.as_view("auth_login"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/logout",
        "view_func": LogoutView.as_view("auth_logout"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/change-password",
        "view_func": ChangePasswordView.as_view("auth_change_password"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/forgot-password",
        "view_func": ForgotPasswordView.as_view("auth_forgot_password"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/reset-password",
        "view_func": ResetPasswordView.as_view("auth_reset_password"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/mfa/enroll",
        "view_func": MFAEnrollView.as_view("auth_mfa_enroll"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/mfa/confirm",
        "view_func": MFAConfirmView.as_view("auth_mfa_confirm"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/mfa/disable",
        "view_func": MFADisableView.as_view("auth_mfa_disable"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/register",
        "view_func": RegisterView.as_view("auth_register"),
        "methods": ["POST"],
    },
    {
        "url_rule": "/google",
        "view_func": GoogleLoginView.as_view("auth_google_login"),
        "methods": ["GET"],
    },
    {
        "url_rule": "/google/callback",
        "view_func": GoogleCallbackView.as_view("auth_google_callback"),
        "methods": ["GET"],
    },
]
