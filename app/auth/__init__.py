from flask import Blueprint
from app.extensions import login_manager
from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

from app.auth import routes
