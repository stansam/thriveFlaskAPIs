from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean, Enum, ForeignKey, SmallInteger, String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db
from app.enums import(
    ThemePreference,
    DashboardLayout,
)
if TYPE_CHECKING:
    from app.models.user import User

class UserPreference(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
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

    def __init__(self, **kwargs: Any) -> None:
        super(UserPreference, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<UserPreference user={self.user_id} theme={self.theme.value}>"
