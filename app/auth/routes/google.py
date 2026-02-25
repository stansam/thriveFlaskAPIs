import logging
from flask import jsonify, redirect, url_for, request
from flask.views import MethodView
from flask_login import login_user
from app.services.auth.service import AuthService
from app.dto.auth.schemas import RegisterRequestDTO
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType, UserRole

# NOTE: Actual Google OAuth logic requires Authlib or direct requests integration. 
# This serves as the structural bounding box implementing standard redirect setups.

logger = logging.getLogger(__name__)

class GoogleAuthorize(MethodView):
    def get(self):
        """Initiates the Google SSO OAuth 2.0 physically bouncing the user to consent screen."""
        track_metric(metric_name="oauth_initiated", category="auth", dimension_key="google")
        
        # TODO: Return a physical redirect URL for the frontend to bind toward
        return jsonify({"redirect_url": "https://accounts.google.com/o/oauth2/v2/auth?..."}), 200


class GoogleCallback(MethodView):
    def post(self):
        """Consumes the Google returned 'code' explicitly mapping it to an identity."""
        code = request.json.get('code')
        if not code:
            return jsonify({"error": "Missing authorization code"}), 400
            
        # TODO: Exchange 'code' for physical JWT claims natively against Google API
        mock_google_user = {
            "email": "google.sso.user@example.com",
            "given_name": "Google",
            "family_name": "User",
            "sub": "google-oauth2|12345"
        }
        
        from app.repository import repositories
        user = repositories.user.find_by_email(mock_google_user['email'])
        
        auth_service = AuthService()
        is_new_user = False
        
        if not user:
            # Safely JIT Provision the SSO user implicitly approving their Google verified Email natively
            import secrets
            payload = RegisterRequestDTO(
                first_name=mock_google_user['given_name'],
                last_name=mock_google_user['family_name'],
                email=mock_google_user['email'],
                password=secrets.token_urlsafe(32), # Unused explicitly
                role=UserRole.CLIENT
            )
            user = auth_service.register_user(payload)
            is_new_user = True
            
            # Auto-verify email natively since Google handled it
            auth_service.verify_email(user.email_verification_token)
            
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