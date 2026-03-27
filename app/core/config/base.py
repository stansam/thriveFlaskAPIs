from __future__ import annotations
import secrets
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseConfig(BaseSettings):
    """
    All configuration fields.  Every value has a sane default for
    development; production overrides must be set via environment variables
    or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          
    )

    # Application
    FLASK_ENV: Literal["development", "testing", "production"] = "development"
    APP_NAME: str = "Thrive Global Travel & Tours"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    TESTING: bool = False
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description="Flask SECRET_KEY. MUST be set explicitly in production.",
    )
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["text", "json"] = "json"

    # Database
    DATABASE_URL: str = "sqlite:///./thrive_dev.db"
    DATABASE_ECHO: bool = False          # set True to log all SQL (dev only)
    DATABASE_POOL_SIZE: int = 10
    DATABASE_POOL_RECYCLE: int = 3600    # seconds; prevents stale connections
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description="Signing key for JWT tokens. MUST be set in production.",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES_SECONDS: int = 3600          # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES_SECONDS: int = 60 * 60 * 24 * 30  # 30 days
    JWT_RESET_TOKEN_EXPIRES_SECONDS: int = 60 * 30        # 30 minutes
    JWT_ISSUER: str = "thrive-travel"
    JWT_AUDIENCE: str = "thrive-travel-api"

    # Security
    # Argon2 password hashing parameters (OWASP recommended minimums)
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_COST: int = 65536    # 64 MiB
    ARGON2_PARALLELISM: int = 4

    # TOTP
    TOTP_ISSUER_NAME: str = "Thrive Travel"
    TOTP_DIGITS: int = 6
    TOTP_INTERVAL: int = 30            # seconds

    # Password policy
    PASSWORD_MIN_LENGTH: int = 10
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False

    # Rate limiting (per IP unless noted)
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_RESET_PER_HOUR: int = 5
    RATE_LIMIT_API_PER_MINUTE: int = 300

    # Redis  (used for: token denylist, rate limiting, optional caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_DENYLIST_DB: int = 1      # separate DB index for JWT denylist
    REDIS_CACHE_DB: int = 2
    REDIS_RATE_LIMIT_DB: int = 3
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5

    # Storage (media uploads)
    STORAGE_BACKEND: Literal["local", "s3", "gcs", "cloudflare"] = "local"
    STORAGE_LOCAL_UPLOAD_DIR: str = "./uploads"
    STORAGE_MAX_FILE_SIZE_MB: int = 10        # per upload
    STORAGE_ALLOWED_IMAGE_TYPES: list[str] = [
        "image/jpeg", "image/png", "image/webp", "image/gif"
    ]
    STORAGE_ALLOWED_DOC_TYPES: list[str] = ["application/pdf"]

    # # S3 / compatible
    # AWS_ACCESS_KEY_ID: str = ""
    # AWS_SECRET_ACCESS_KEY: str = ""
    # AWS_S3_BUCKET: str = ""
    # AWS_S3_REGION: str = "us-east-1"
    # AWS_S3_ENDPOINT_URL: str | None = None    # for MinIO / Backblaze

    # # Cloudflare R2
    # CLOUDFLARE_R2_ACCOUNT_ID: str = ""
    # CLOUDFLARE_R2_ACCESS_KEY: str = ""
    # CLOUDFLARE_R2_SECRET_KEY: str = ""
    # CLOUDFLARE_R2_BUCKET: str = ""
    # CLOUDFLARE_R2_PUBLIC_URL: str = ""

    # CDN base URL (prepended to storage_key to form cdn_url)
    CDN_BASE_URL: str = "http://localhost:5000/uploads"

    # Email (SendGrid primary; SMTP fallback)
    EMAIL_BACKEND: Literal["sendgrid", "smtp", "console"] = "console"
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@thriveglobaltravel.com"
    SENDGRID_FROM_NAME: str = "Thrive Global Travel & Tours"
    SENDGRID_WEBHOOK_SIGNING_KEY: str = ""

    # SMTP fallback
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True

    # WhatsApp (WATI)
    WATI_API_URL: str = ""
    WATI_API_KEY: str = ""
    WATI_WEBHOOK_TOKEN: str = ""

    # Kayak / RapidAPI (flight search)
    RAPIDAPI_KEY: str = ""
    RAPIDAPI_KAYAK_HOST: str = "kayak.p.rapidapi.com"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_SUPPORTS_CREDENTIALS: bool = True

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 25
    MAX_PAGE_SIZE: int = 200

    # Background jobs (if Celery is added later)
    CELERY_BROKER_URL: str = "redis://localhost:6379/4"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/5"

    # Validators

    @field_validator("SECRET_KEY", "JWT_SECRET_KEY", mode="before")
    @classmethod
    def _warn_weak_secret(cls, v: str, info) -> str:
        if len(v) < 32:
            import warnings
            warnings.warn(
                f"{info.field_name} is shorter than 32 characters. "
                "Use a cryptographically random value in production.",
                stacklevel=4,
            )
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalise_db_url(cls, v: str) -> str:
        # SQLAlchemy 2.x requires "postgresql+psycopg2://" not "postgres://"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        return v

    @property
    def sqlalchemy_engine_options(self) -> dict:
        """Passed directly to Flask-SQLAlchemy SQLALCHEMY_ENGINE_OPTIONS."""
        opts: dict = {}
        if "sqlite" not in self.DATABASE_URL:
            opts = {
                "pool_size": self.DATABASE_POOL_SIZE,
                "pool_recycle": self.DATABASE_POOL_RECYCLE,
                "pool_timeout": self.DATABASE_POOL_TIMEOUT,
                "max_overflow": self.DATABASE_MAX_OVERFLOW,
                "pool_pre_ping": True,   # detects stale connections
            }
        return opts

    @property
    def flask_config(self) -> dict:
        """
        Returns a dict suitable for `app.config.from_mapping(...)`.
        Only Flask-recognised keys are included here; app-specific settings
        are accessed directly via `settings.<FIELD>`.
        """
        return {
            "SECRET_KEY": self.SECRET_KEY,
            "DEBUG": self.DEBUG,
            "TESTING": self.TESTING,
            "SQLALCHEMY_DATABASE_URI": self.DATABASE_URL,
            "SQLALCHEMY_ECHO": self.DATABASE_ECHO,
            "SQLALCHEMY_ENGINE_OPTIONS": self.sqlalchemy_engine_options,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
