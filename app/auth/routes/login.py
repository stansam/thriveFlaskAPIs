from flask import request, jsonify
from flask.views import MethodView
from flask_login import login_user
from app.auth.schemas.login import LoginSchema
from app.extensions import db
from app.repository.user.services import UserService
from marshmallow import ValidationError

class Login(MethodView):
    def post(self):
        schema = LoginSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as err:
            return jsonify(err.messages), 400

        service = UserService(db.session)
        user = service.authenticate_user(data['email'], data['password'])

        if user:
            login_user(user, remember=data.get('remember_me', False))
            return jsonify({
                "message": "Login successful",
                "user": user.to_dict()
            }), 200
        
        return jsonify({"message": "Invalid email or password"}), 401