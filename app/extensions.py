# app/extensions.py
"""
Flask extension singletons.

Extensions are instantiated here WITHOUT a Flask app object (the
"two-phase" pattern).  The `init_app(app)` call happens inside the
application factory in `app/__init__.py`.

This avoids circular imports: extensions can be imported by models,
services, and blueprints without any of them needing to import the
Flask `app` object.

Import pattern in the rest of the codebase:
    from app.extensions import db, migrate, cors, limiter, cache

Never import from `app` directly in models or services — that creates
a circular dependency.
"""

from flask_cors import CORS
from flask_limiter import Limiter
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager
from app.models.base import db  # noqa: F401  (re-export for convenience)

def _rate_limit_key() -> str:
    """Rate limit by the proxy-aware real client IP."""
    from flask import has_request_context
    from app.core.utils import get_user_ip as _get_user_ip
    return _get_user_ip() if has_request_context() else "no-request"

migrate = Migrate()
cors = CORS()
limiter = Limiter(
    key_func=_rate_limit_key,
    storage_uri=None,           # set in init_app via app.config
    strategy="fixed-window",
)
cache = Cache()
login_manager = LoginManager()