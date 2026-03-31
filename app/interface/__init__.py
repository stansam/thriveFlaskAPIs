"""
Service registry initialization.

Instantiates core services using the pre-existing repository singletons,
a SQLAlchemy-backed Unit of Work, and a Redis-backed token denylist.
"""
from app.repository import user_repo, user_preference_repo
from app.core.unit_of_work import SQLAlchemyUnitOfWork
from app.core.token_denylist import RedisTokenDenylist
from app.interface.auth import AuthService
from app.interface.user import UserService
from app.interface.audit import audit_service


class _ServiceRegistry:
    """
    Lazily instantiated singleton registry for all Application Domain Services.

    All services are constructed once at import time. Dependencies are injected
    explicitly — services never resolve their own dependencies.
    """
    auth: AuthService = AuthService(
        user_repo=user_repo,
        audit_service=audit_service,
        uow=SQLAlchemyUnitOfWork(),
        denylist=RedisTokenDenylist(),
    )

    user: UserService = UserService(
        user_repo=user_repo,
        user_preference_repo=user_preference_repo,
        audit_service=audit_service,
        uow=SQLAlchemyUnitOfWork(),
    )


# Exported singleton
registry = _ServiceRegistry()

# Aliases
auth_service = registry.auth
user_service = registry.user

__all__ = [
    "registry",
    "auth_service",
    "user_service",
]
