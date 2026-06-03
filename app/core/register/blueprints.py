from flask import Flask
from app.api.v1.user import user_bp
from app.api.v1.auth import auth_bp

def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints."""
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    # from app.blueprints.clients_bp  import clients_bp
    # from app.blueprints.packages_bp import packages_bp
    # from app.blueprints.bookings_bp import bookings_bp
    # from app.blueprints.payments_bp import payments_bp
    # from app.blueprints.fees_bp     import fees_bp
    # from app.blueprints.media_bp    import media_bp
    # from app.blueprints.loyalty_bp  import loyalty_bp
    # from app.blueprints.referrals_bp import referrals_bp
    # from app.blueprints.notifications_bp import notifications_bp
    # from app.blueprints.reports_bp  import reports_bp
    # from app.blueprints.audit_bp    import audit_bp
    # from app.blueprints.flights_bp  import flights_bp
