from flask import Flask
import os
from app.config.register_blueprints import register_blueprints
from app.config import config

def create_app(app=os.environ.get("FLASK_ENV", "development")) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[app])
    register_blueprints(app)
    return app