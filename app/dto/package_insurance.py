from __future__ import annotations
from decimal import Decimal
from typing import Annotated
from pydantic import Field, field_validator
from .common import AuditFieldsMixin, StrictRequestModel

class PackageInsuranceCreateRequest(StrictRequestModel):
    provider_name:    Annotated[str, Field(min_length=1, max_length=150)]
    policy_name:      Annotated[str, Field(min_length=1, max_length=150)]
    coverage_details: str | None = None
    premium_usd:      Annotated[Decimal, Field(ge=Decimal("0"))] = Decimal("0.00")
    per_person_rate:  Annotated[Decimal, Field(ge=Decimal("0"))] = Decimal("0.00")
    is_active:        bool = True

    @field_validator("premium_usd", "per_person_rate", mode="before")
    @classmethod
    def coerce_decimal(cls, v) -> Decimal:
        return Decimal(str(v))

class PackageInsuranceUpdateRequest(StrictRequestModel):
    provider_name:    str | None = None
    policy_name:      str | None = None
    coverage_details: str | None = None
    premium_usd:      Decimal | None = None
    per_person_rate:  Decimal | None = None
    is_active:        bool | None = None

class PackageInsuranceResponse(AuditFieldsMixin):
    package_id:       str
    provider_name:    str
    policy_name:      str
    coverage_details: str | None
    premium_usd:      Decimal
    per_person_rate:  Decimal
    is_active:        bool
