from flask import request, jsonify
from flask.views import MethodView
from app.auth.schemas.verify_email import VerifyEmailSchema
from app.extensions import db
from app.repository.user.services import UserService
from marshmallow import ValidationError

class VerifyEmail(MethodView):
    def post(self):
        schema = VerifyEmailSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        user_service = UserService(db.session)
        try:
            token = data['token']
            user_id = request.json.get('user_id')
            
            if not user_id:
                return jsonify({"user_id": ["Missing data for required field."]}), 400

            service = UserService(db.session)
            user = service.VerifyUserEmail(user_id, token)
            
            return jsonify({
                "message": "Email verified successfully.",
                "user": user.to_dict()
            }), 200
            
        except Exception as e:
            return jsonify({"message": str(e)}), 400
