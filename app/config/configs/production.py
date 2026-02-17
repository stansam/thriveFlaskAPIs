import os
from app.config.configs.base import BaseConfig

class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # TODO:Ensure SECRET_KEY is set in production
    if not SECRET_KEY:
        pass