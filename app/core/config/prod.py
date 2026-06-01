from .base import BaseConfig
from typing import Literal
from pydantic import model_validator
from pydantic_settings import SettingsConfigDict

class ProductionConfig(BaseConfig):
    FLASK_ENV: str = "production"
    DEBUG: bool = False
    LOG_FORMAT: Literal["text", "json"] = "json"

    @model_validator(mode="after")
    def _validate_production_requirements(self) -> "ProductionConfig":
        errors: list[str] = []

        if self.SECRET_KEY.startswith("dev-") or len(self.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be a secure random value ≥32 chars.")
        if self.JWT_SECRET_KEY.startswith("dev-") or len(self.JWT_SECRET_KEY) < 32:
            errors.append("JWT_SECRET_KEY must be a secure random value ≥32 chars.")
        if "sqlite" in self.DATABASE_URL:
            errors.append("DATABASE_URL must not be SQLite in production.")
        if not self.REDIS_URL:
            errors.append("REDIS_URL is required in production.")

        if errors:
            raise ValueError(
                "Production configuration errors:\n" +
                "\n".join(f"  • {e}" for e in errors)
            )
        return self