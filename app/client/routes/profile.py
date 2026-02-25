import logging
from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user, logout_user
from marshmallow import ValidationError
from app.client.schemas.profile import UpdateProfileSchema, UpdatePreferencesSchema
from app.dto.user.schemas import UpdateProfileDTO, UpdatePreferencesDTO
from app.services.user.service import UserService
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType

logger = logging.getLogger(__name__)

class ProfileView(MethodView):
    decorators = [login_required]

    def get(self):
        """Fetch active user identity natively via the JWT/Session."""
        return jsonify(current_user.to_dict()), 200

    def put(self):
        """Consume profile updates merging partial structures."""
        schema = UpdateProfileSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        user_service = UserService()
        dto = UpdateProfileDTO(**data)
        
        try:
            updated_user = user_service.update_profile(current_user.id, dto)
            
            track_metric(metric_name="profile_updated", category="client")
            log_audit(
                action=AuditAction.UPDATE,
                entity_type=EntityType.USER,
                entity_id=current_user.id,
                user_id=current_user.id,
                description="Profile demographics patched natively",
                changes=data
            )
            return jsonify({
                "message": "Profile updated successfully.",
                "user": updated_user.to_dict()
            }), 200
            
        except ValueError as ve:
             return jsonify({"error": str(ve)}), 400


class PreferencesView(MethodView):
    decorators = [login_required]

    def put(self):
        schema = UpdatePreferencesSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400
            
        user_service = UserService()
        dto = UpdatePreferencesDTO(**data)
        
        try:
             updated_user = user_service.update_preferences(current_user.id, dto)
             track_metric(metric_name="preferences_updated", category="client")
             return jsonify({
                 "message": "Preferences safely saved.",
                 "preferences": updated_user.preferences
             }), 200
        except ValueError as ve:
             return jsonify({"error": str(ve)}), 400

class AccountDeletionView(MethodView):
    decorators = [login_required]
    
    def delete(self):
        """Irreversible GDPR wipe mapping explicit service boundaries."""
        user_service = UserService()
        user_id = current_user.id
        
        # Fire farewell notification PRE-Deletion
        try:
            ns = NotificationService()
            ns.dispatch_notification(DispatchNotificationDTO(
                user_id=user_id,
                trigger_event="ACCOUNT_DELETED",
                context={"first_name": current_user.first_name}
            ))
        except Exception as e:
            logger.error(f"Failed to dispatch final GDPR warning: {e}")
        
        try:
            # Drop DB ties, anonymize strings structurally, lock Auth constraints
            user_service.delete_account(user_id)
            track_metric(metric_name="account_deleted", category="client", value=1.0)
            log_audit(
                action=AuditAction.UPDATE, # Typically 'UPDATE' marking `is_deleted`=True or scrambling
                entity_type=EntityType.USER,
                entity_id=user_id,
                user_id=user_id,
                description="User invoked permanent GDPR deletion request."
            )
            
            # Formally expire session logic natively
            logout_user()
            
            return jsonify({"message": "Account scheduled for complete erasure. Farewell!"}), 200
            
        except ValueError as ve:
             return jsonify({"error": str(ve)}), 400
