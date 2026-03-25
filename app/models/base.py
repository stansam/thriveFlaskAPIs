# models/base.py
"""
Shared SQLAlchemy instance and the AuditMixin that every model inherits from.

AuditMixin provides:
  - id            : UUID primary key (server-side default via gen_random_uuid() in Postgres,
                    or Python uuid4 fallback for SQLite / tests)
  - created_at    : UTC timestamp set once on INSERT
  - updated_at    : UTC timestamp refreshed on every UPDATE via onupdate
  - created_by_id : FK → users.id — the user who created the record (nullable so seed /
                    system-generated rows can exist without a user)
  - updated_by_id : FK → users.id — the last user who touched the record

Usage
-----
    class MyModel(db.Model, AuditMixin):
        __tablename__ = "my_models"
        ...

The mixin deliberately does NOT include `__tablename__` — subclasses own that.
"""

import uuid
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, String, event
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Single declarative base shared across the entire application."""
    pass


db = SQLAlchemy(model_class=Base)

# Helpers
def _uuid_default() -> str:
    """Returns a new UUID4 string.  Used as Python-side column default so that
    SQLite (used in tests / local dev) also gets proper UUIDs without needing
    a Postgres server-side function."""
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

# AuditMixin
class AuditMixin:
    """
    Abstract mixin — NOT a mapped model on its own.

    Columns
    -------
    id             Primary key, UUID stored as CHAR(36) for broad DB compat.
                   On Postgres the column type is native UUID.
    created_at     Set once at insert time; never updated thereafter.
    updated_at     Auto-refreshed on every update via SQLAlchemy onupdate.
    created_by_id  Soft FK to users.id — nullable for system/seed records.
    updated_by_id  Soft FK to users.id — nullable.

    Notes
    -----
    *  `created_by_id` / `updated_by_id` are declared as plain String FKs
       rather than relationship()-bearing columns inside the mixin to avoid
       circular import issues.  Each concrete model that needs to navigate
       to the User object should declare the relationship explicitly.

    *  We use `String(36)` as the universal column type so the same model
       file works against both SQLite and PostgreSQL without conditional
       type switching.  On Postgres you can migrate to native UUID with an
       ALTER COLUMN at any point.
    """

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_uuid_default,
        doc="UUID primary key.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        doc="UTC timestamp of record creation.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
        doc="UTC timestamp of last modification.",
    )

    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True, name="fk_%(table_name)s_created_by"),
        nullable=True,
        index=True,
        doc="User who created this record.",
    )

    updated_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL", use_alter=True, name="fk_%(table_name)s_updated_by"),
        nullable=True,
        index=True,
        doc="User who last modified this record.",
    )

    # Convenience helpers
    def touch(self, user_id: str) -> None:
        """Manually stamp updated_at / updated_by_id without a full save.
        Useful in service-layer code before a session.flush()."""
        self.updated_at = _utcnow()
        self.updated_by_id = user_id

    def set_creator(self, user_id: str) -> None:
        """Set created_by_id and updated_by_id together on first creation."""
        self.created_by_id = user_id
        self.updated_by_id = user_id

    def to_audit_dict(self) -> dict:
        """Return a lightweight dict suitable for AuditLog snapshots."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by_id": self.created_by_id,
            "updated_by_id": self.updated_by_id,
        }
