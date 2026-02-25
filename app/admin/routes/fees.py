import logging
from flask import request, jsonify
from flask.views import MethodView
from app.admin.routes.dashboard import admin_required
from app.admin.schemas.fees import ServiceFeeSchema
from marshmallow import ValidationError
from app.utils.audit_log import log_audit
from app.utils.analytics import track_metric
from app.models.enums import AuditAction, EntityType
from flask_login import current_user

logger = logging.getLogger(__name__)

class ManageFeesView(MethodView):
    decorators = [admin_required]

    def post(self):
        """Create or configure physical structural Service Fee rule layers."""
        schema = ServiceFeeSchema()
        try:
             data = schema.load(request.json)
        except ValidationError as err:
             return jsonify(err.messages), 400

        try:
             from app.repository import repositories
             from app.models.fee_rule import FeeRule
             from app.extensions import db
             
             rule = FeeRule(
                 name=data['name'],
                 amount=data['amount'],
                 currency=data['currency'],
                 rule_type=data['rule_type'],
                 is_active=data['is_active']
             )
             
             db.session.add(rule)
             db.session.commit()
             
             log_audit(
                 action=AuditAction.CREATE, # Or UPDATE natively mapping against existing ID
                 entity_type=EntityType.FEE_RULE,
                 entity_id=rule.id,
                 user_id=current_user.id,
                 description=f"Generated global pricing tier modifier: {rule.name} ({rule.amount} {rule.rule_type})"
             )
             track_metric("service_fee_updated", category="admin")

             return jsonify({
                 "message": "Markup structurally ingested.",
                 "fee": rule.to_dict()
             }), 201

        except Exception as e:
             logger.error(f"Rule layer setup bounds failed explicitly: {e}")
             return jsonify({"error": str(e)}), 400
