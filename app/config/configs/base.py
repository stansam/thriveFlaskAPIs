import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key-change-me'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True

    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    FRONTEND_DASHBOARD_URL = os.environ.get('FRONTEND_DASHBOARD_URL', f"{FRONTEND_URL}/dashboard")
    FRONTEND_VERIFY_EMAIL_URL = os.environ.get('FRONTEND_VERIFY_EMAIL_URL', f"{FRONTEND_URL}/verify-email")
    FRONTEND_RESET_PASSWORD_URL = os.environ.get('FRONTEND_RESET_PASSWORD_URL', f"{FRONTEND_URL}/reset-password")

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
