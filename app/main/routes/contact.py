import logging
from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from app.main.schemas.contact import ContactFormSchema
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO
from app.utils.analytics import track_metric

logger = logging.getLogger(__name__)

class ContactView(MethodView):
    def post(self):
        schema = ContactFormSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        try:
             ns = NotificationService()
             
             # Track metrics for top-of-funnel lead ingest
             track_metric("contact_form_submitted", category="main")
             
             # Dispense dual notification structural setup 
             # 1. Thank you receipt
             ns.dispatch_notification(DispatchNotificationDTO(
                 user_id=None, # Anonymous lead
                 email_override=data['email'],
                 trigger_event="CONTACT_RECEIPT",
                 context={"name": data['name']}
             ))
             
             # 2. Alert Admins 
             from app.repository import repositories
             admin = repositories.user.get_admin_user()
             
             if admin:
                 ns.dispatch_notification(DispatchNotificationDTO(
                     user_id=admin.id,
                     trigger_event="NEW_CONTACT_LEAD",
                     context={
                         "lead_name": data['name'],
                         "lead_email": data['email'],
                         "subject": data['subject'],
                         "message": data['message']
                     }
                 ))
                 
             return jsonify({
                 "message": "Thank you for reaching out! A representative will contact you shortly."
             }), 201

        except Exception as e:
             logger.error(f"Contact form unhandled structural fault: {e}")
             return jsonify({"error": "Failed to process contact inquiry."}), 500
