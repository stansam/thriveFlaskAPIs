from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean, ForeignKey, Numeric, SmallInteger, String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db

if TYPE_CHECKING:
    from app.models.package import TravelPackage

class PackagePriceTier(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "package_price_tiers"

    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("travel_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(
        String(100), nullable=False,
        doc='e.g. "Solo", "Couple", "Group (6+)", "Add Flights"',
    )
    price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_per: Mapped[str] = mapped_column(
        String(30), nullable=False, default="person"
    )
    min_participants: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    max_participants: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, doc="NULL = no upper bound."
    )
    is_add_on: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        doc="True for optional add-ons like flights or insurance.",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    package: Mapped["TravelPackage"] = relationship(
        "TravelPackage", back_populates="price_tiers"
    )

    def __init__(self, **kwargs: Any) -> None:
        super(PackagePriceTier, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<PackagePriceTier {self.label} ${self.price_usd}>"