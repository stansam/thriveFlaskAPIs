from flask import jsonify, request
from flask_login import logout_user
from flask.views import MethodView
import logging

logger = logging.getLogger(__name__)

class Logout(MethodView):
    def post(self):
        try:
            logout_user()
            return jsonify({"message": "Logout successful"}), 200
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return jsonify({"message": "An error occurred"}), 500