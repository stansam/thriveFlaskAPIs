from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean, Numeric, String, Text, ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, db

if TYPE_CHECKING:
    from app.models.package import TravelPackage

class PackageInsurance(db.Model, AuditMixin):  # type: ignore[name-defined, misc]
    __tablename__ = "package_insurances"

    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("travel_packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(150), nullable=False)
    policy_name: Mapped[str] = mapped_column(String(150), nullable=False)
    coverage_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    premium_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    per_person_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    package: Mapped["TravelPackage"] = relationship(
        "TravelPackage",
        back_populates="insurance_options",
    )

    def __init__(self, **kwargs: Any) -> None:
        super(PackageInsurance, self).__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<PackageInsurance {self.provider_name} - {self.policy_name}>"
