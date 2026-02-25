import logging
from flask import jsonify
from flask.views import MethodView
from app.utils.analytics import track_metric

logger = logging.getLogger(__name__)

class DepartureListView(MethodView):
    def get(self):
        from app.repository import repositories
        
        # Extract immediate slots cleanly bound towards physical departure tables
        departures = repositories.package.get_upcoming_departures(limit=25)
        
        track_metric("departure_slots_viewed", category="main")
        
        return jsonify({
            "departures": [d.to_dict() for d in departures]
        }), 200
