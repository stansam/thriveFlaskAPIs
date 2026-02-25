import logging
from flask import jsonify, request
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from app.models.enums import UserRole
from app.admin.schemas.analytics import DashboardQuerySchema

logger = logging.getLogger(__name__)

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.ADMIN:
             return jsonify({"error": "Forbidden: Global Administrator clearance required."}), 403
        return f(*args, **kwargs)
    return decorated_function

class DashboardView(MethodView):
    decorators = [admin_required]

    def get(self):
        schema = DashboardQuerySchema()
        try:
            data = schema.load(request.args.to_dict()) if request.args else {}
        except ValidationError as err:
            return jsonify(err.messages), 400

        from app.repository import repositories
        from datetime import datetime, timezone, timedelta
        from app.models.enums import BookingStatus, UserRole, PaymentStatus
        
        # Calculate a 30-day trailing window dynamically
        now = datetime.now(timezone.utc).date()
        thirty_days_ago = now - timedelta(days=30)
        
        total_revenue = repositories.booking.calculate_total_revenue_by_period(start_date=thirty_days_ago, end_date=now)
        total_bookings = len(repositories.booking.get_bookings_by_status(BookingStatus.CONFIRMED)) # In reality this should be a fast count, but using existing repo
        active_users = repositories.user.count_active_users_by_role(UserRole.CLIENT)
        pending_payments = repositories.payment.count_by_status(PaymentStatus.PENDING)

        metrics = {
             "total_revenue": round(total_revenue, 2),
             "total_bookings": total_bookings,
             "active_users": active_users,
             "pending_payments": pending_payments
        }
                
        return jsonify({
             "message": "Dashboard aggregations fetched natively.",
             "metrics": metrics
        }), 200
