from flask import Blueprint
from app.admin.routes.booking import admin_booking_bp

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

admin_bp.register_blueprint(admin_booking_bp, url_prefix='/')
