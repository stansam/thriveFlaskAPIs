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
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_caching import Cache
from app.models.base import db  # noqa: F401  (re-export for convenience)

migrate = Migrate()
cors = CORS()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],          # no default; limits are per-route
    storage_uri=None,           # set in init_app via app.config
    strategy="fixed-window",
)
cache = Cache()
