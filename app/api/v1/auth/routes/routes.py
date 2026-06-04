# app/api/v1/auth/routes/routes.py
"""
Auth API route views using Flask MethodView.
"""
from __future__ import annotations

from flask import request, redirect
from flask.views import MethodView
from flask_login import login_required, current_user
from app.extensions import limiter
from app.core.config import settings
from app.core.security import csrf_protect

from app.core.dependencies import get_services
from app.core.utils import get_user_ip, get_user_agent
from app.core.errors.handlers import BadRequestError
from app.core.responses import (
    success_response,
    no_content_response,
    created_response,
)
from app.dto import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    UserRegistrationRequest,
)
from app.api.v1.auth.schemas import (
    LoginSchema,
    PasswordChangeSchema,
    ForgotPasswordSchema,
    ResetPasswordSchema,
    MFAConfirmSchema,
    MFADisableSchema,
    RegisterUserSchema,
)
from app.core.redis import get_redis
import secrets
import httpx
import logging
from app.core.logging import get_logger

logger = get_logger(__name__)


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
    decorators = [login_required, csrf_protect]

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
        csrf_protect,
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
    decorators = [login_required, csrf_protect]

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
    decorators = [login_required, csrf_protect]

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
    decorators = [login_required, csrf_protect]

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


class RegisterView(MethodView):
    """POST /api/v1/auth/register — Public Agent self-registration."""
    decorators = [
        limiter.limit("5/hour"),  # Stricter rate limit on signup
    ]

    def post(self) -> tuple:
        json_data = request.get_json()
        if json_data is None:
            raise BadRequestError("Invalid JSON payload.")

        payload = RegisterUserSchema().load(json_data)
        data = UserRegistrationRequest.model_validate(payload)
        ip_address = get_user_ip()
        user_agent = get_user_agent()

        result = get_services().auth.register_user(
            data=data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return created_response(
            data=result.model_dump(mode="json"),
            message="Registration successful.",
        )


class GoogleLoginView(MethodView):
    """GET /api/v1/auth/google — Initiates OAuth consent redirect."""
    
    def get(self) -> tuple:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise BadRequestError("Google OAuth is not configured on this server.")
            
        state = secrets.token_urlsafe(32)
        redis_client = get_redis()
        # Store state in Redis with 5 minute expiration
        redis_client.set(f"oauth_state:{state}", "1", ex=settings.OAUTH_STATE_TTL_SECONDS)

        # Build Google authorization URL
        google_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
            "&response_type=code"
            "&scope=openid email profile"
            f"&state={state}"
        )
        return redirect(google_url)


class GoogleCallbackView(MethodView):
    """
    GET /api/v1/auth/google/callback — OAuth redirection landing.
    
    Redirect Flow Explanation:
    --------------------------
    1. Google redirects the user's browser back to this callback route with an authorization `code` and `state`.
    2. The server validates the `state` against the Redis token store to protect against CSRF attacks.
    3. The server exchanges the authorization `code` for an access token via Google's token endpoint.
    4. The server retrieves the user's Google profile using the access token.
    5. The server checks if the email is verified, then verifies, links, or registers the user (agent) via `verify_google_oauth`.
    6. Flask-Login session cookie is set on the browser upon successful login.
    7. Finally, the server issues a 302 redirect back to the frontend redirect landing page:
       - On success: redirects to `FRONTEND_URL/auth/callback?status=success`
       - On error: redirects to `FRONTEND_URL/auth/callback?status=error&message=<error_message>`
    """
    decorators = [
        limiter.limit("20/minute"),  # Prevent DOS on callback endpoint
    ]

    def get(self) -> tuple:
        code = request.args.get("code")
        state = request.args.get("state")

        if not code or not state:
            logger.warning("Google callback invoked without code or state parameter.")
            return redirect(f"{settings.FRONTEND_URL}/auth/callback?status=error&message=Missing+parameters")

        # 1. Validate state token in Redis
        redis_client = get_redis()
        state_key = f"oauth_state:{state}"
        if not redis_client.exists(state_key):
            logger.warning("Google callback invoked with invalid or expired state token.")
            return redirect(f"{settings.FRONTEND_URL}/auth/callback?status=error&message=Invalid+state")
        redis_client.delete(state_key)  # Single-use

        # 2. Exchange authorization code for token
        try:
            token_resp = httpx.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                timeout=10.0,
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()
            access_token = tokens["access_token"]

            # 3. Retrieve user profile info
            profile_resp = httpx.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
            profile_resp.raise_for_status()
            profile = profile_resp.json()
        except Exception as exc:
            logger.exception("Failed token exchange or profile fetch with Google.")
            return redirect(f"{settings.FRONTEND_URL}/auth/callback?status=error&message=Communication+failure")

        # 4. Verify Google confirmed the email
        if not profile.get("email_verified"):
            logger.warning("Google account email not verified: %s", profile.get("email"))
            return redirect(f"{settings.FRONTEND_URL}/auth/callback?status=error&message=Email+not+verified")

        # 5. Handle Login / Self-Registration Operations
        try:
            ip_address = get_user_ip()
            user_agent = get_user_agent()
            
            get_services().auth.verify_google_oauth(
                profile=profile,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return redirect(f"{settings.FRONTEND_URL}/auth/callback?status=success")
        except Exception as exc:
            logger.warning("Google OAuth verification failed: %s", exc)
            return redirect(f"{settings.FRONTEND_URL}/auth/callback?status=error&message=Authentication+failed")

