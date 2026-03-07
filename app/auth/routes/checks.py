from flask import jsonify
from flask.views import MethodView
from flask_login import current_user

class IsAuthenticated(MethodView):
    def get(self): 
        #return jsonify({
        #        "authenticated": bool(current_user.is_authenticated)
        #    }), 200
        return jsonify(current_user.is_authenticated), 200

class CurrentUserView(MethodView):
    def get(self):
        if not current_user.is_authenticated:
            return jsonify({
                "message": "Not authenticated"
            }), 401

        user_dict = {
                "email": current_user.email,
                "name": "{current_user.first_name} {current_user.last_name}",
                "is_admin": current_user.is_admin()
            }
        return jsonify({
            "user": user__dict()
        }), 200
