"""
Service registry initialization.

Instantiates core services using the pre-existing repository registries.
"""

from app.repository import user_repo, audit_repo
from app.interface.auth import AuthService

class _ServiceRegistry:
    """
    Lazily instantiated singleton registry for all Application Domain Services.
    """
    auth: AuthService = AuthService(user_repo=user_repo, audit_repo=audit_repo)

# Exported singleton
registry = _ServiceRegistry()

# Aliases
auth_service = registry.auth

__all__ = [
    "registry",
    "auth_service",
]
