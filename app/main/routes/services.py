import logging
from flask import jsonify
from flask.views import MethodView
from app.utils.analytics import track_metric
from app.services.registry import ServiceRegistry 
logger = logging.getLogger(__name__)

class ServicesView(MethodView):
    def get(self):
        services_func = ServiceRegistry.service
        services = services_func.get_all_services()
        
        track_metric("services_viewed", category="main")
        
        return jsonify({
            "services": [s.to_dict() for s in services]
        }), 200