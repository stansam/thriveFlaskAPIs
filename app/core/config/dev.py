from .base import BaseConfig
from typing import Literal
from pydantic_settings import SettingsConfigDict

class DevelopmentConfig(BaseConfig):
    FLASK_ENV: Literal["development"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: Literal["text", "json"] = "text"
    DATABASE_ECHO: bool = False
    EMAIL_BACKEND: Literal["sendgrid", "smtp", "console"] = "console"


