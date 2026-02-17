import os
from dotenv import load_dotenv

load_dotenv()

from app.config.configs.base import BaseConfig

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dev.db'

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "mock-client-id") 
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "mock-client-secret")