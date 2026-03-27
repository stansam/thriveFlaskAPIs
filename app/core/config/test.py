from .base import BaseConfig
from typing import Literal
from pydantic_settings import SettingsConfigDict

class TestingConfig(BaseConfig):
    FLASK_ENV: Literal["testing"] = "testing"
    TESTING: bool = True
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES_SECONDS: int = 60    # 1 minute — fast expiry in tests
    JWT_REFRESH_TOKEN_EXPIRES_SECONDS: int = 120
    JWT_RESET_TOKEN_EXPIRES_SECONDS: int = 60
    EMAIL_BACKEND: Literal["sendgrid", "smtp", "console"] = "console"
    STORAGE_BACKEND: Literal["local", "s3", "gcs", "cloudflare"] = "local"
    LOG_LEVEL: str = "WARNING"
    # Use fixed secrets in tests so JWT tokens are reproducible
    SECRET_KEY: str = "testing-secret-key-do-not-use-in-production-12345"
    JWT_SECRET_KEY: str = "testing-jwt-secret-key-do-not-use-in-production-67890"
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 1000   # effectively disable in tests

