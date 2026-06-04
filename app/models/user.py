from typing import TYPE_CHECKING, Any

from datetime import datetime, timezone
from sqlalchemy import Boolean, Enum, String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import UserRole
from app.core.security.encryption import encrypt_field, decrypt_field

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
    _mfa_secret: Mapped[str | None] = mapped_column(
        "mfa_secret",
        String(256),
        nullable=True,
        doc="TOTP seed (base-32, encrypted at rest). NULL = MFA not enrolled.",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    google_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        doc="Google OAuth unique subject ID (sub claim).",
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
    def mfa_secret(self) -> str | None:
        """Return decrypted MFA secret (or None)."""
        return decrypt_field(self._mfa_secret)

    @mfa_secret.setter
    def mfa_secret(self, value: str | None) -> None:
        """Encrypt and store MFA secret."""
        self._mfa_secret = encrypt_field(value)

    @property
    def mfa_is_enrolled(self) -> bool:
        return bool(self.mfa_secret and not self.mfa_secret.endswith(":pending"))

    @property
    def mfa_is_pending(self) -> bool:
        return bool(self.mfa_secret and self.mfa_secret.endswith(":pending"))

    @property
    def is_locked(self) -> bool:
        """True if account is currently under brute-force lockout."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    def __init__(self, **kwargs: Any) -> None:
        super(User, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role.value}]>"
