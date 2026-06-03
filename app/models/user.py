from typing import TYPE_CHECKING, Any

from datetime import datetime
from sqlalchemy import Boolean, Enum, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import UserRole

if TYPE_CHECKING:
    from app.models.audit import AuditLog
    from app.models.user_preference import UserPreference

class User(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
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
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="actor",
        foreign_keys="AuditLog.actor_id",
        lazy="write_only",
        passive_deletes=True,
    )
    preference: Mapped["UserPreference | None"] = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="UserPreference.user_id",
    )

    @property
    def mfa_is_enrolled(self) -> bool:
        return bool(self.mfa_secret and not self.mfa_secret.endswith(":pending"))

    @property
    def mfa_is_pending(self) -> bool:
        return bool(self.mfa_secret and self.mfa_secret.endswith(":pending"))

    def __init__(self, **kwargs: Any) -> None:
        super(User, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role.value}]>"
