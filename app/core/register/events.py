# app/core/register/events.py
"""
Register event subscribers during application startup.
"""
from flask import Flask

def _register_event_handlers(app: Flask) -> None:
    """Import events modules to run their decorators at startup."""
    import app.interface.user.events  # noqa: F401
