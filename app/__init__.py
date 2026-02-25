from flask import Flask
import os
from app.config.register_blueprints import register_blueprints
from app.config import config
from app.extensions import db, migrate

def create_app(config_name=os.environ.get("FLASK_ENV", "development")) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from app.extensions import login_manager, cache
    login_manager.init_app(app)
    
    # Configure generic simplistic cache locally for the GDS API limiting buffers
    app.config.setdefault('CACHE_TYPE', 'SimpleCache')
    cache.init_app(app)
    
    register_blueprints(app)
    return app