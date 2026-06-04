from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from app.enums import InclusionType
from .common import AuditFieldsMixin, StrictRequestModel

from .media import PackageMediaResponse

# PACKAGE HIGHLIGHT
class PackageHighlightCreateRequest(StrictRequestModel):
    text:          Annotated[str, Field(min_length=1, max_length=500)]
    icon:          Annotated[str | None, Field(default=None, max_length=50)]
    display_order: int = 0

class PackageHighlightResponse(AuditFieldsMixin):
    package_id:    str
    text:          str
    icon:          str | None
    display_order: int

class PackageHighlightUpdateRequest(StrictRequestModel):
    text:          str | None = None
    icon:          str | None = None
    display_order: int | None = None

# PACKAGE INCLUSION
class PackageInclusionCreateRequest(StrictRequestModel):
    inclusion_type:  InclusionType
    label:           Annotated[str, Field(min_length=1, max_length=300)]
    notes:           Annotated[str | None, Field(default=None, max_length=500)]
    extra_cost_usd:  Decimal | None = None
    display_order:   int = 0

class PackageInclusionResponse(AuditFieldsMixin):
    package_id:     str
    inclusion_type: InclusionType
    label:          str
    notes:          str | None
    extra_cost_usd: Decimal | None
    display_order:  int

class PackageInclusionUpdateRequest(StrictRequestModel):
    inclusion_type:  InclusionType | None = None
    label:           str | None = None
    notes:           str | None = None
    extra_cost_usd:  Decimal | None = None
    display_order:   int | None = None

# PACKAGE ITINERARY DAY
class PackageItineraryDayCreateRequest(StrictRequestModel):
    day_number:     Annotated[int, Field(ge=1)]
    title:          Annotated[str, Field(min_length=1, max_length=300)]
    description:    str | None = None
    activities:     str | None = None
    meals_included: Annotated[str | None, Field(default=None, max_length=100)]
    accommodation:  Annotated[str | None, Field(default=None, max_length=300)]

class PackageItineraryDayUpdateRequest(StrictRequestModel):
    title:          str | None = None
    description:    str | None = None
    activities:     str | None = None
    meals_included: str | None = None
    accommodation:  str | None = None

class PackageItineraryDayResponse(AuditFieldsMixin):
    package_id:     str
    day_number:     int
    title:          str
    description:    str | None
    activities:     str | None
    meals_included: str | None
    accommodation:  str | None
    # Media
    media: list[PackageMediaResponse] = []

PackageItineraryDayResponse.model_rebuild()

# PACKAGE PRICE TIER
class PackagePriceTierCreateRequest(StrictRequestModel):
    label:             Annotated[str, Field(min_length=1, max_length=100)]
    price_usd:         Annotated[Decimal, Field(gt=Decimal("0"))]
    price_per:         Annotated[str, Field(default="person", max_length=30)]
    min_participants:  Annotated[int, Field(ge=1)] = 1
    max_participants:  Annotated[int | None, Field(default=None, ge=1)]
    is_add_on:         bool = False
    is_active:         bool = True

    @field_validator("price_usd", mode="before")
    @classmethod
    def coerce_decimal(cls, v) -> Decimal:
        return Decimal(str(v))

class PackagePriceTierUpdateRequest(StrictRequestModel):
    label:            str | None = None
    price_usd:        Decimal | None = None
    price_per:        str | None = None
    min_participants: int | None = None
    max_participants: int | None = None
    is_add_on:        bool | None = None
    is_active:        bool | None = None

class PackagePriceTierResponse(AuditFieldsMixin):
    package_id:       str
    label:            str
    price_usd:        Decimal
    price_per:        str
    min_participants: int
    max_participants: int | None
    is_add_on:        bool
    is_active:        bool