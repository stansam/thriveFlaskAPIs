from flask import request, jsonify, url_for
from flask.views import MethodView
from app.auth.schemas.register import RegisterSchema
from app.extensions import db
from app.repository.user.services import UserService
from app.repository.email.services import EmailService
from app.repository.notification.services import NotificationService
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
        email_service = EmailService(db.session)
        notification_service = NotificationService(db.session)

        # Separate confirm_password as it's not needed for creation
        if 'confirm_password' in data:
            del data['confirm_password']

        try:
            user = user_service.CreateUser(data)
            
            # 1. Send Welcome Email
            # Generate verification token first?
            # For now, just welcome email. Real flow might ask to verify first.
            try:
                # Assuming we have a 'welcome_email' template or we send direct
                # "Welcome {{ name }}!"
                email_service.send_email(
                    to_email=user.email,
                    subject="Welcome to Thrive Travels!",
                    # body_html=f"<h1>Welcome {user.first_name}!</h1><p>We are excited to have you on board.</p>"
                    body_html=email_service.render_template(
                        template_name="welcome_email.html",
                        context={
                            "user": user,
                        }
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send welcome email: {e}")

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
            admin = user_service.GetAdminUser()
            try:
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
            return jsonify({"message": str(e)}), 400
