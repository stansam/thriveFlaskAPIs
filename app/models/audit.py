from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import AuditActionType

if TYPE_CHECKING:
    from app.models.user import User

class AuditLog(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    """
    Append-only event log row.

    actor_id      — the User who performed the action (NULL = system job)
    action        — what happened
    entity_type   — which model was affected (table name, e.g. "booking")
    entity_id     — PK of the affected row
    before_snapshot — JSON of the entity state before the change
    after_snapshot  — JSON of the entity state after the change
    description   — free-text summary useful in admin activity feeds
    ip_address    — IP of the actor's request
    user_agent    — browser/client of the actor's request
    """

    __tablename__ = "audit_logs"

    actor_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="NULL for automated / system-initiated events.",
    )
    action: Mapped[AuditActionType] = mapped_column(
        Enum(AuditActionType, name="audit_action_type_enum"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc='Model name, e.g. "booking", "client", "payment".',
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        doc="PK of the affected entity. NULL for login/logout events.",
    )
    before_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="JSON snapshot of the record before the action.",
    )
    after_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="JSON snapshot of the record after the action.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable summary, e.g. 'Booking TG-001 confirmed by admin'.",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        doc="IPv4 or IPv4-mapped IPv6 address of the request.",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    actor: Mapped["User | None"] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[actor_id],
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog {self.action.value} "
            f"{self.entity_type}/{self.entity_id} "
            f"by={self.actor_id}>"
        )
