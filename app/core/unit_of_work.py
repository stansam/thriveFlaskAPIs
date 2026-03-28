"""
Unit of Work pattern.

Provides a clean transaction boundary that services can own without
reaching into repository internals. The `IUnitOfWork` abstract interface
keeps the application layer decoupled from SQLAlchemy specifics.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Type


class IUnitOfWork(ABC):
    """Abstract Unit of Work for transaction management.

    Usage
    -----
        with uow:
            repo.save(entity)
            uow.commit()
    """

    @abstractmethod
    def __enter__(self) -> "IUnitOfWork":
        """Enter the transaction context."""
        ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the transaction context; rolls back on unhandled exception."""
        ...

    @abstractmethod
    def commit(self) -> None:
        """Persist all staged changes to the database."""
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Discard all staged changes."""
        ...


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """SQLAlchemy-backed Unit of Work using the Flask-SQLAlchemy session.

    Ties into `db.session` from `app.models.base`, which is scoped to
    the current request context by Flask-SQLAlchemy.
    """

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        # Flask-SQLAlchemy handles session teardown at end of request.

    def commit(self) -> None:
        """Commit the current session to the database."""
        from app.models.base import db
        db.session.commit()

    def rollback(self) -> None:
        """Roll back the current session."""
        from app.models.base import db
        db.session.rollback()
