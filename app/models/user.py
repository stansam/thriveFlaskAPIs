# models/user.py
"""
Internal staff / admin users of the platform.

Clients (customers) are a separate model — see client.py.
This model represents Dr. Edna and future employees who operate the system.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, db
from app.enums import UserRole

if TYPE_CHECKING:
    from .audit import AuditLog
    from .user_preference import UserPreference

class User(db.Model, AuditMixin):
    """
    Platform operator / internal staff member.

    Security notes
    --------------
    - `password_hash` stores a bcrypt / argon2 digest — never plaintext.
    - `is_active` gates authentication; soft-delete disabled users
      without losing audit history.
    - `mfa_secret` stores a TOTP seed (base-32 encoded); NULL means MFA
      is not enrolled.
    """

    __tablename__ = "users"

    # Identity
    email: Mapped[str] = mapped_column(
        String(254),
        unique=True,
        nullable=False,
        index=True,
        doc="Primary login credential; RFC-5321 max length.",
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Auth
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.AGENT,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mfa_secret: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="TOTP seed (base-32). NULL = MFA not enrolled.",
    )
    last_login_at: Mapped[db.DateTime | None] = mapped_column(
        db.DateTime(timezone=True), nullable=True
    )

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="actor",
        foreign_keys="AuditLog.actor_id",
        lazy="dynamic",
    )
    preference: Mapped["UserPreference | None"] = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="UserPreference.user_id",
    )

    # Repr
    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role.value}]>"
