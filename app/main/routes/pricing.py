import logging
from flask import jsonify
from flask.views import MethodView
from app.utils.analytics import track_metric

logger = logging.getLogger(__name__)

class PricingTierView(MethodView):
    def get(self):
        from app.repository import repositories
        
        # Pull global public active SaaS subscription tiers naturally mapping UI displays
        plans = repositories.subscription.get_all_active_plans()
        
        track_metric("pricing_viewed", category="main")
        
        return jsonify({
            "tiers": [p.to_dict() for p in plans]
        }), 200
