import logging
import os
import requests
from flask import jsonify, redirect, url_for, request, current_app
from flask.views import MethodView
from flask_login import login_user
from app.services.auth.service import AuthService
from app.dto.auth.schemas import RegisterRequestDTO
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType, UserRole

logger = logging.getLogger(__name__)

class GoogleAuthorize(MethodView):
    def get(self):
        """Initiates the Google SSO OAuth 2.0 physically bouncing the user to consent screen."""
        track_metric(metric_name="oauth_initiated", category="auth", dimension_key="google")
        
        client_id = current_app.config.get('GOOGLE_CLIENT_ID', os.environ.get('GOOGLE_CLIENT_ID', 'sandbox_id'))
        redirect_uri = request.args.get('redirect_uri', f"{request.host_url}api/auth/google/callback")
        
        url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=email%20profile"
        )
        return jsonify({"redirect_url": url}), 200


class GoogleCallback(MethodView):
    def post(self):
        """Consumes the Google returned 'code' explicitly mapping it to an identity."""
        code = request.json.get('code')
        redirect_uri = request.json.get('redirect_uri', f"{request.host_url}api/auth/google/callback")
        
        if not code:
            return jsonify({"error": "Missing authorization code"}), 400
            
        try:
            client_id = current_app.config.get('GOOGLE_CLIENT_ID', os.environ.get('GOOGLE_CLIENT_ID', 'sandbox_id'))
            client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET', os.environ.get('GOOGLE_CLIENT_SECRET', 'sandbox_secret'))
            
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=10
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            
            user_response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            user_response.raise_for_status()
            google_user = user_response.json()
            
            email = google_user.get("email")
            given_name = google_user.get("given_name", "Google")
            family_name = google_user.get("family_name", "User")
            
            if not email:
                return jsonify({"error": "Google profile missing definitively bound email address natively."}), 400
                
        except requests.RequestException as e:
            logger.error(f"Google OAuth explicit HTTP exchange faulted cleanly: {e}")
            return jsonify({"error": "Failed contacting external Authorization boundaries."}), 401
            
        from app.repository import repositories
        user = repositories.user.find_by_email(email)
        
        auth_service = AuthService()
        is_new_user = False
        
        if not user:
            from app.models.user import User
            import secrets
            
            user_dict = {
                "first_name": given_name,
                "last_name": family_name,
                "email": email,
                "role": UserRole.CLIENT,
                "email_verified": True # Dynamically mapped trusting Google inherently natively
            }
            user = User(**user_dict)
            user.set_password(secrets.token_urlsafe(32))
            
            user = repositories.user.save_user(user)
            is_new_user = True
            
            log_audit(
                action=AuditAction.CREATE,
                entity_type=EntityType.USER,
                entity_id=user.id,
                user_id=user.id, 
                description="Account instantly created via Google SSO."
            )
            
        # Complete session binding universally
        login_user(user, remember=True)
        track_metric(metric_name="oauth_completed", category="auth", dimension_key="google")
        
        return jsonify({
            "message": "SSO Login successful",
            "user": user.to_dict(),
            "new_registration": is_new_user
        }), 200