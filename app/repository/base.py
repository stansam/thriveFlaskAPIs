# repositories/base.py
"""
Generic typed repository base.

Architecture
------------
Every concrete repository inherits `BaseRepository[M]` where M is the
SQLAlchemy model type.  The base provides:

  • Full CRUD   : get, get_or_404, list, create, update, delete, bulk_create
  • Pagination  : paginate() returns a typed Page[M] dataclass
  • Filtering   : filter_by_kwargs, exists, count
  • Soft audit  : all mutating methods accept an optional `actor_id` and
                  stamp `created_by_id` / `updated_by_id` automatically
  • Transaction : save() / delete() wrap flush; callers own the commit
                  boundary via the Flask-SQLAlchemy session

Why not use Flask-SQLAlchemy's built-in query interface?
  The 2.x `db.session.execute(select(...))` style is used throughout
  rather than the legacy `Model.query` API, which is deprecated and
  incompatible with async SQLAlchemy if the project ever migrates.

Why repositories instead of fat service classes?
  - Testable: swap the repo for an in-memory fake in unit tests
  - Composable: services orchestrate multiple repos in one transaction
  - Auditable: a single choke-point stamps created_by / updated_by
  - Queryable: complex list queries live in one place, not scattered
    across route handlers
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Generic, Type, TypeVar

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Select, func, select
from sqlalchemy.exc import NoResultFound
from werkzeug.exceptions import NotFound

from app.models.base import AuditMixin, db as _db

from app.core.logging import get_logger

logger = get_logger(__name__)


M = TypeVar("M", bound=AuditMixin)

@dataclass
class Page(Generic[M]):
    """
    Pagination envelope returned by BaseRepository.paginate().

    items        — the rows for the current page
    total        — total matching rows across all pages
    page         — current 1-indexed page number
    per_page     — rows per page
    total_pages  — ceil(total / per_page)
    has_next     — True if a next page exists
    has_prev     — True if a previous page exists
    """
    items: list[M]
    total: int
    page: int
    per_page: int

    @property
    def total_pages(self) -> int:
        return max(1, math.ceil(self.total / self.per_page)) if self.per_page else 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    def to_dict(self, serializer=None) -> dict:
        """Convenience: returns a JSON-serialisable dict.
        Pass a serializer callable (e.g. a DTO's model_validate) to
        transform each item."""
        items = [serializer(i) for i in self.items] if serializer else self.items
        return {
            "items": items,
            "total": self.total,
            "page": self.page,
            "per_page": self.per_page,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
        }


class BaseRepository(Generic[M]):
    """
    Generic repository providing typed database access for one model class.

    Usage
    -----
        class BookingRepository(BaseRepository[Booking]):
            model = Booking

            def find_by_reference(self, ref: str) -> Booking | None:
                stmt = select(Booking).where(Booking.reference_number == ref)
                return self._session.execute(stmt).scalar_one_or_none()

    All write methods accept `actor_id: str | None = None` and stamp the
    audit columns when the model inherits AuditMixin.

    The `_session` property resolves the SQLAlchemy session from the
    current Flask application context on every access, so repositories
    are safe to instantiate once at module level (singleton pattern).
    """

    model: Type[M]          # must be set by subclass
    db: SQLAlchemy = _db    # injectable for testing

    @property
    def _session(self):
        return self.db.session

    def get(self, record_id: str) -> M | None:
        """Return the record or None if not found."""
        return self._session.get(self.model, record_id)

    def get_or_404(self, record_id: str, description: str | None = None) -> M:
        """Return the record or raise werkzeug 404."""
        obj = self.get(record_id)
        if obj is None:
            raise NotFound(description or f"{self.model.__name__} not found.")
        return obj

    def get_by(self, **kwargs: Any) -> M | None:
        """Return the first record matching all kwargs or None."""
        stmt = select(self.model).filter_by(**kwargs)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_by_or_404(self, **kwargs: Any) -> M:
        obj = self.get_by(**kwargs)
        if obj is None:
            raise NotFound(f"{self.model.__name__} not found.")
        return obj

    def all(self) -> list[M]:
        """Return all rows. Avoid on large tables — prefer paginate()."""
        stmt = select(self.model)
        return list(self._session.execute(stmt).scalars().all())

    def list_by(self, **kwargs: Any) -> list[M]:
        """Return all rows matching kwargs."""
        stmt = select(self.model).filter_by(**kwargs)
        return list(self._session.execute(stmt).scalars().all())

    def paginate(
        self,
        stmt: Select | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Page[M]:
        """
        Execute a SELECT statement with LIMIT/OFFSET pagination.

        If `stmt` is None, selects all rows of the model.
        Pass a fully-constructed `select(Model).where(...).order_by(...)`
        statement for filtered / sorted pages.

        Returns a typed Page[M] instance.
        """
        if stmt is None:
            stmt = select(self.model)

        # Total count — reuse the WHERE clause, strip ORDER BY
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total: int = self._session.execute(count_stmt).scalar_one()

        # Paginated rows
        page = max(1, page)
        per_page = max(1, min(per_page, 200))   # hard ceiling: 200
        offset = (page - 1) * per_page
        rows = list(
            self._session.execute(
                stmt.limit(per_page).offset(offset)
            ).scalars().all()
        )

        return Page(items=rows, total=total, page=page, per_page=per_page)

    def exists(self, **kwargs: Any) -> bool:
        stmt = select(func.count()).select_from(
            select(self.model).filter_by(**kwargs).subquery()
        )
        return self._session.execute(stmt).scalar_one() > 0

    def count(self, stmt: Select | None = None) -> int:
        if stmt is None:
            stmt = select(self.model)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        return self._session.execute(count_stmt).scalar_one()

    def create(self, actor_id: str | None = None, **kwargs: Any) -> M:
        """
        Instantiate, stamp audit columns, add to session, flush.
        Does NOT commit — callers control the transaction boundary.
        """
        obj = self.model(**kwargs)
        if actor_id and hasattr(obj, "set_creator"):
            obj.set_creator(actor_id)
        self._session.add(obj)
        self._session.flush()
        return obj

    def update(
        self,
        obj: M,
        actor_id: str | None = None,
        **kwargs: Any,
    ) -> M:
        """
        Apply field updates, re-stamp updated_by / updated_at, flush.
        Only fields present in kwargs are updated.
        """
        for key, value in kwargs.items():
            if not hasattr(obj, key):
                raise AttributeError(
                    f"{type(obj).__name__} has no attribute '{key}'. "
                    f"Check for typos in the update call."
                )
            setattr(obj, key, value)
        if actor_id and hasattr(obj, "touch"):
            obj.touch(actor_id)
        self._session.flush()
        return obj

    def save(self, obj: M, actor_id: str | None = None) -> M:
        """
        Add an already-mutated instance to the session and flush.
        Useful when the caller has directly set attributes.
        """
        if actor_id and hasattr(obj, "touch"):
            obj.touch(actor_id)
        self._session.add(obj)
        self._session.flush()
        return obj

    def delete(self, obj: M) -> None:
        """Hard-delete from the session and flush."""
        self._session.delete(obj)
        self._session.flush()

    def delete_by_id(self, record_id: str) -> bool:
        """Delete by PK. Returns True if a record was found and deleted."""
        obj = self.get(record_id)
        if obj is None:
            return False
        self.delete(obj)
        return True

    def bulk_create(
        self,
        items: list[dict],
        actor_id: str | None = None,
    ) -> list[M]:
        """
        Create multiple records in a single flush.
        `items` is a list of dicts; each dict is kwargs for one record.
        """
        objs: list[M] = []
        for kwargs in items:
            obj = self.model(**kwargs)
            if actor_id and hasattr(obj, "set_creator"):
                obj.set_creator(actor_id)
            self._session.add(obj)
            objs.append(obj)
        self._session.flush()
        return objs

    def bulk_update(
        self,
        objects: list[M],
        actor_id: str | None = None,
    ) -> list[M]:
        """Flush a list of already-mutated objects."""
        for obj in objects:
            if actor_id and hasattr(obj, "touch"):
                obj.touch(actor_id)
            self._session.add(obj)
        self._session.flush()
        return objects