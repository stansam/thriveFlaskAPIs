# app/api/v1/auth/routes/routes.py
"""
Auth API route views using Flask MethodView.
"""
from __future__ import annotations

from flask import request
from flask.views import MethodView
from flask_login import login_required, current_user
from app.extensions import limiter
from app.core.config import settings

from app.core.dependencies import get_services
from app.core.utils import get_user_ip, get_user_agent
from app.core.errors.handlers import BadRequestError
from app.core.responses import (
    success_response,
    no_content_response,
)
from app.dto import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
)
from app.api.v1.auth.schemas import (
    LoginSchema,
    PasswordChangeSchema,
    ForgotPasswordSchema,
    ResetPasswordSchema,
    MFAConfirmSchema,
    MFADisableSchema,
)


class LoginView(MethodView):
    """POST /api/v1/auth/login"""
    decorators = [
        limiter.limit(f"{settings.RATE_LIMIT_LOGIN_PER_MINUTE}/minute"),
    ]

    def post(self) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")

        payload = LoginSchema().load(json_data)
        data = LoginRequest.model_validate(payload)
        ip_address = get_user_ip()
        user_agent = get_user_agent()

        result = get_services().auth.login(
            data=data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return success_response(
            data=result.model_dump(mode="json"),
            message="Login successful.",
        )


class LogoutView(MethodView):
    """POST /api/v1/auth/logout"""
    decorators = [login_required]

    def post(self) -> tuple:
        ip_address = get_user_ip()
        user_agent = get_user_agent()
        get_services().auth.logout(
            user_id=current_user.get_id(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return no_content_response()


class ChangePasswordView(MethodView):
    """POST /api/v1/auth/change-password"""
    decorators = [
        limiter.limit("20/minute"),
        login_required,
    ]

    def post(self) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")

        payload = PasswordChangeSchema().load(json_data)
        data = PasswordChangeRequest.model_validate(payload)
        ip_address = get_user_ip()
        user_agent = get_user_agent()

        get_services().auth.change_password(
            user_id=current_user.get_id(),
            data=data,
            actor_id=current_user.get_id(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return success_response(message="Password changed successfully.")


class ForgotPasswordView(MethodView):
    """POST /api/v1/auth/forgot-password"""
    decorators = [
        limiter.limit(f"{settings.RATE_LIMIT_RESET_PER_HOUR}/hour"),
    ]

    def post(self) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")

        payload = ForgotPasswordSchema().load(json_data)
        ip_address = get_user_ip()
        user_agent = get_user_agent()

        result = get_services().auth.request_password_reset(
            email=payload["email"],
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return success_response(
            data=result.model_dump(mode="json"),
            message=result.message,
        )


class ResetPasswordView(MethodView):
    """POST /api/v1/auth/reset-password"""
    decorators = [
        limiter.limit("10/minute"),
    ]

    def post(self) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")

        payload = ResetPasswordSchema().load(json_data)
        data = PasswordResetRequest.model_validate(payload)
        ip_address = get_user_ip()
        user_agent = get_user_agent()

        get_services().auth.reset_password(
            data=data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return success_response(
            message="Password has been reset. You may now log in.",
        )


class MFAEnrollView(MethodView):
    """POST /api/v1/auth/mfa/enroll"""
    decorators = [login_required]

    def post(self) -> tuple:
        result = get_services().auth.enroll_mfa(
            user_id=current_user.get_id(),
            actor_id=current_user.get_id(),
        )
        return success_response(
            data=result.model_dump(mode="json"),
            message="Scan the QR code with your authenticator app, then confirm.",
        )


class MFAConfirmView(MethodView):
    """POST /api/v1/auth/mfa/confirm"""
    decorators = [login_required]

    def post(self) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")

        payload = MFAConfirmSchema().load(json_data)
        ip_address = get_user_ip()
        user_agent = get_user_agent()

        get_services().auth.confirm_mfa_enrollment(
            user_id=current_user.get_id(),
            totp_code=payload["totp_code"],
            actor_id=current_user.get_id(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return success_response(message="MFA successfully activated.")


class MFADisableView(MethodView):
    """POST /api/v1/auth/mfa/disable"""
    decorators = [login_required]

    def post(self) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")

        payload = MFADisableSchema().load(json_data)
        ip_address = get_user_ip()
        user_agent = get_user_agent()

        get_services().auth.disable_mfa(
            user_id=current_user.get_id(),
            totp_code=payload["totp_code"],
            actor_id=current_user.get_id(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return success_response(message="MFA has been disabled.")
