import logging
from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from app.client.schemas.subscription import SubscriptionUpgradeSchema
from app.dto.subscription.schemas import UpgradePlanDTO
from app.services.subscription.service import SubscriptionService
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType
from app.services.notification.service import NotificationService
from app.dto.notification.schemas import DispatchNotificationDTO

logger = logging.getLogger(__name__)

class SubscriptionUpgradeView(MethodView):
    decorators = [login_required]

    def post(self):
        schema = SubscriptionUpgradeSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        from app.repository import repositories
        
        # Resolve User's implicitly active subscription constraints natively
        subscription = repositories.subscription.get_active_subscription(
            entity_type=EntityType.USER, # Adjust if B2B bindings operate entirely differently
            entity_id=current_user.id
        )
        
        if not subscription:
            return jsonify({"error": "Identified bound active subscription missing natively."}), 404
            
        subscription_service = SubscriptionService()
        payload = UpgradePlanDTO(
            subscription_id=subscription.id,
            new_plan_id=data['new_plan_id']
        )
        
        try:
            upgraded_sub = subscription_service.upgrade_plan(payload)
            track_metric("subscription_upgraded", category="client")
            log_audit(
                 action=AuditAction.UPDATE,
                 entity_type=EntityType.SUBSCRIPTION,
                 entity_id=upgraded_sub.id,
                 user_id=current_user.id,
                 description="User successfully bounced their active plan boundaries tier."
            )
            try:
                ns = NotificationService()
                ns.dispatch_notification(DispatchNotificationDTO(
                    user_id=current_user.id,
                    trigger_event="SUBSCRIPTION_UPGRADED",
                    context={"plan_name": upgraded_sub.plan.name}
                ))
            except Exception as e:
                 logger.error(f"Subscription alert fail bound: {e}")

            return jsonify({
                 "message": "Subscription tier significantly upgraded.",
                 "subscription": upgraded_sub.to_dict()
            }), 200

        except ValueError as ve:
             return jsonify({"error": str(ve)}), 400
