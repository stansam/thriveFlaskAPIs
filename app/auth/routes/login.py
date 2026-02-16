from flask import request, jsonify
from flask_login import login_user
from app.models import User
from app.auth.schemas import LoginSchema
class login:
    def post(self) -> jsonify:
        data = LoginSchema().load(request.json())