# models/preference.py
"""
User & Client preference models.

Two separate preference models because Users (staff) and Clients
(customers) have fundamentally different configurable surfaces:

UserPreference   — admin/agent UI settings (theme, timezone, dashboard
                   layout, default filters, notification subscriptions)

ClientPreference — customer-facing settings (communication channel
                   preference, marketing opt-in, language, currency
                   display, document format)

Both are strictly 1:1 with their parent.  They are created lazily on
first settings update and queried with a LEFT JOIN so missing rows
return sensible defaults without requiring a seed job.

Design decision: store individual typed columns rather than a single
JSONB "settings" blob.  This allows:
  - SQL-level querying ("all clients who prefer WhatsApp")
  - Indexed filtering for notification fanout jobs
  - Alembic-tracked column additions with proper defaults
  - No application-layer schema validation on untyped JSON
"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, Enum, ForeignKey, SmallInteger, String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, db
from app.enums import(
    ThemePreference,
    DashboardLayout,
)
if TYPE_CHECKING:
    from .user import User

class UserPreference(db.Model, AuditMixin):
    """
    Persisted UI and workflow preferences for a platform operator (User).

    Notification flags control which system events trigger an in-app
    or email notification for this user.  All default to True so that
    a new admin misses nothing; they opt-out individually.

    `default_booking_channel` pre-fills the booking channel dropdown
    when this agent creates a new booking.

    `items_per_page` controls pagination defaults across all list views.
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # UI
    theme: Mapped[ThemePreference] = mapped_column(
        Enum(ThemePreference, name="theme_pref_enum"),
        nullable=False,
        default=ThemePreference.SYSTEM,
    )
    timezone: Mapped[str] = mapped_column(
        String(60), nullable=False, default="UTC",
        doc='IANA timezone string, e.g. "America/New_York".',
    )
    language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en",
        doc="BCP-47 language tag.",
    )
    dashboard_layout: Mapped[DashboardLayout] = mapped_column(
        Enum(DashboardLayout, name="dashboard_layout_enum"),
        nullable=False,
        default=DashboardLayout.OVERVIEW,
    )
    items_per_page: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=25,
        doc="Rows per page across all paginated list views.",
    )

    # Workflow defaults
    default_booking_channel: Mapped[str] = mapped_column(
        String(30), nullable=False, default="whatsapp",
        doc="Pre-filled channel when creating a new booking.",
    )
    show_ticket_cost_column: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="Show underlying ticket cost column in booking list.",
    )
    auto_send_confirmation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="Automatically send confirmation notification when booking is CONFIRMED.",
    )

    # Notification subscriptions (all in-app + email)
    notify_new_booking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_payment_received: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_booking_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_booking_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_new_client: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notify_referral_qualified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_subscription_renewal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_low_stock_alert: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="Alert when a package approaches max_participants.",
    )

    # Relationship
    user: Mapped["User"] = relationship(
        "User", back_populates="preference", uselist=False,
        foreign_keys=[user_id],
    )

    def __repr__(self) -> str:
        return f"<UserPreference user={self.user_id} theme={self.theme.value}>"
