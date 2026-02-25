from flask import request, jsonify
from flask.views import MethodView
from app.auth.schemas.register import RegisterSchema
from app.extensions import db
from app.services.user.service import UserService
from app.services.notification.service import NotificationService
from app.utils.email import send_welcome_email
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class Register(MethodView):
    def post(self):
        schema = RegisterSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        user_service = UserService(db.session)
        notification_service = NotificationService(db.session)

        if 'confirm_password' in data:
            del data['confirm_password']

        try:
            user = user_service.CreateUser(data)
            
            send_welcome_email(user)

            log_audit(
                action=AuditAction.CREATE,
                entity_type=EntityType.USER,
                entity_id=user.id,
                user_id=user.id, 
                description=f"User {user.email} registered via email."
            )
            track_metric(metric_name="user_registered", category="auth")

            try:
                notification_service.send_notification(
                    user_id=user.id,
                    title="Welcome to Thrive!",
                    message="Your account has been successfully created. Explore our latest packages.",
                    notification_type="general",
                    priority="normal"
                )
            except Exception as e:
                logger.error(f"Failed to send user notification: {e}")

            try:
                admin = user_service.GetAdminUser()
                if admin:
                    notification_service.send_notification(
                        user_id=admin.id,
                        title="New User Registration",
                        message=f"New user {user.first_name} {user.last_name} has registered.",
                        notification_type="general",
                        priority="normal"
                    )
            except Exception as e:
                logger.error(f"Failed to send admin notification: {e}")
            
            return jsonify({
                "message": "Registration successful",
                "user": user.to_dict()
            }), 201

        except Exception as e:
            logger.error(f"Registration error: {e}")
            return jsonify({"message": str(e)}), 400
