import os
from functools import lru_cache


from app.core.config.base import BaseConfig
from app.core.config.dev import DevelopmentConfig
from app.core.config.test import TestingConfig
from app.core.config.prod import ProductionConfig

_CONFIG_MAP: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
}

@lru_cache(maxsize=1)
def get_config() -> BaseConfig:
    """
    Return the application configuration singleton.

    Reads `APP_ENV` from the environment (default: "development").
    The result is cached so instantiation + .env parsing only happens once.

    To force a reload in tests:
        get_config.cache_clear()
    """
    env = os.getenv("FLASK_ENV", "development").lower()
    config_class = _CONFIG_MAP.get(env, DevelopmentConfig)
    return config_class()

#module-level singleton
settings: BaseConfig = get_config()