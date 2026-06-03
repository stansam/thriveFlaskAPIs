# app/__init__.py
"""
Flask Application Factory.

Usage
-----
    # Standard startup (WSGI / development server)
    from app import create_app
    app = create_app()

    # With an explicit environment override
    app = create_app("testing")

    # Flask CLI (flask run / flask db upgrade / flask seed)
    # FLASK_APP=wsgi:app flask run

Architecture
------------
This factory follows the "create_app" pattern so that:
  1. Multiple isolated instances can be created (required for testing).
  2. Extensions are initialised with `init_app(app)` — no circular imports.
  3. Configuration is injected at creation time, not at import time.

Extension initialisation order matters:
  db → migrate → cors → limiter → cache → blueprints → error handlers → middleware

All models must be imported before `db.create_all()` / Alembic migration
so SQLAlchemy's metadata is populated.  The `_register_models()` call
handles this.
"""

from __future__ import annotations

import logging
import logging.config
import os
import sys

from flask import Flask

from app.core.config import get_config
from app.core.errors import register_error_handlers
from app.core.register import (
    _register_blueprints,
    _register_cli_commands,
    _register_health_check,
    _register_event_handlers,
)
from app.core.logging import _configure_logging

def _register_models() -> None:
    import app.models

def create_app(env: str | None = None, test_config: dict | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Parameters
    ----------
    env         Override the APP_ENV environment variable.
    test_config Override any config values (useful in tests):
                    app = create_app("testing", {"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})

    Returns
    -------
    Flask application instance, fully configured and ready to serve.
    """
    # ── 1. Resolve config ──────────────────────────────────────────────
    if env:
        os.environ["FLASK_ENV"] = env
        get_config.cache_clear()

    config = get_config()

    # ── 2. Configure logging early ─────────────────────────────────────
    _configure_logging(config)
    logger = logging.getLogger(__name__)
    logger.info(
        "Creating Flask app [env=%s version=%s]",
        config.FLASK_ENV,
        config.APP_VERSION,
    )

    # ── 3. Create Flask instance ────────────────────────────────────────
    app = Flask(
        __name__,
        instance_relative_config=False,
    )

    # ── 4. Load configuration ───────────────────────────────────────────
    app.config.from_mapping(config.flask_config)

    # Apply test overrides (must happen after from_mapping)
    if test_config:
        app.config.from_mapping(test_config)

    # ── 5. Ensure models are registered before extensions ───────────────
    _register_models()

    # ── 6. Initialise extensions ────────────────────────────────────────
    from app.models.base import db
    from app.extensions import migrate, cors, limiter, cache, login_manager

    db.init_app(app)

    migrate.init_app(app, db, directory="migrations")

    cors.init_app(
        app,
        origins=config.CORS_ORIGINS,
        supports_credentials=config.CORS_SUPPORTS_CREDENTIALS,
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
        methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    )

    limiter.init_app(app)

    login_manager.init_app(app)

    if cache is not None:
        app.config["CACHE_TYPE"]            = "RedisCache"
        app.config["CACHE_REDIS_URL"]       = config.REDIS_URL
        app.config["CACHE_DEFAULT_TIMEOUT"] = 300
        cache.init_app(app)

    with app.app_context():
        from app.interface import _ServiceRegistry
        app.extensions['services'] = _ServiceRegistry()
    # ── 7. Register blueprints ──────────────────────────────────────────
    _register_blueprints(app)
    _register_event_handlers(app)

    # ── 8. Register error handlers ──────────────────────────────────────
    register_error_handlers(app)

    # ── 9. Register middleware ──────────────────────────────────────────
    from app.core.middleware import register_middleware
    register_middleware(app)

    # ── 10. Health check ────────────────────────────────────────────────
    _register_health_check(app)

    # ── 11. CLI commands ────────────────────────────────────────────────
    _register_cli_commands(app)

    # ── 12. Create tables in dev/test (Alembic handles production) ──────
    if config.FLASK_ENV in ("development", "testing"):
        with app.app_context():
            try:
                db.create_all()
                logger.debug("db.create_all() completed.")
            except Exception as exc:
                logger.warning("db.create_all() failed (may be fine if using Alembic): %s", exc)

    logger.info(
        "App ready. DB=%s CORS=%s",
        config.DATABASE_URL.split("@")[-1] if "@" in config.DATABASE_URL else config.DATABASE_URL,
        config.CORS_ORIGINS,
    )
    return app