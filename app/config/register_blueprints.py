from app.auth import auth_bp
from app.manage import manage_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(manage_bp)