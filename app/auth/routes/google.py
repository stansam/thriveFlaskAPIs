from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_user
from app.auth.schemas.google import GoogleOAuthSchema
from app.extensions import db
from app.repository.user.services import UserService
from marshmallow import ValidationError

class Google(MethodView):
    def post(self):
        schema = GoogleOAuthSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        user_service = UserService(db.session)
        try:
            user = user_service.google_oauth(data['id_token'])
            
            if user:
                login_user(user, remember=data.get('remember_me', False))
                return jsonify({
                    "message": "Google login successful",
                    "user": user.to_dict()
                }), 200
            else:
                return jsonify({"message": "Google authentication failed"}), 401
                
        except Exception as e:
            return jsonify({"message": str(e)}), 400