# dtos/package.py
"""
TravelPackage and all child entity DTOs.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from app.enums import PackageStatus, InclusionType
from app.dto.common import AuditFieldsMixin, StrictRequestModel, ResponseModel
from app.dto.media import PackageMediaResponse
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

# TRAVEL PACKAGE  (aggregate root)
class TravelPackageCreateRequest(StrictRequestModel):
    title:               Annotated[str, Field(min_length=2, max_length=300)]
    slug:                Annotated[str | None, Field(default=None, max_length=320,
                             pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
    tagline:             Annotated[str | None, Field(default=None, max_length=500)]
    description:         str | None = None
    status:              PackageStatus = PackageStatus.DRAFT
    destination_country: Annotated[str, Field(min_length=2, max_length=100)]
    destination_city:    Annotated[str | None, Field(default=None, max_length=100)]
    region:              Annotated[str | None, Field(default=None, max_length=100)]
    duration_days:       Annotated[int, Field(ge=1)]
    duration_nights:     Annotated[int, Field(ge=0)]
    base_price_usd:      Annotated[Decimal, Field(gt=Decimal("0"))]
    price_per:           Annotated[str, Field(default="person", max_length=30)]
    min_participants:    Annotated[int, Field(ge=1)] = 1
    max_participants:    Annotated[int | None, Field(default=None, ge=1)]
    flights_includable:  bool = False
    insurance_includable: bool = False
    is_featured:         bool = False
    # Nested creation (optional batch with parent)
    highlights:  list[PackageHighlightCreateRequest] = []
    inclusions:  list[PackageInclusionCreateRequest] = []
    itinerary:   list[PackageItineraryDayCreateRequest] = []
    price_tiers: list[PackagePriceTierCreateRequest] = []

    @field_validator("base_price_usd", mode="before")
    @classmethod
    def coerce_decimal(cls, v) -> Decimal:
        return Decimal(str(v))

    @field_validator("slug", mode="before")
    @classmethod
    def auto_slug(cls, v, info):
        if v:
            return v.lower().strip()
        return v

class TravelPackageUpdateRequest(StrictRequestModel):
    title:               str | None = None
    slug:                str | None = None
    tagline:             str | None = None
    description:         str | None = None
    status:              PackageStatus | None = None
    destination_country: str | None = None
    destination_city:    str | None = None
    region:              str | None = None
    duration_days:       int | None = None
    duration_nights:     int | None = None
    base_price_usd:      Decimal | None = None
    price_per:           str | None = None
    min_participants:    int | None = None
    max_participants:    int | None = None
    flights_includable:  bool | None = None
    insurance_includable: bool | None = None
    is_featured:         bool | None = None

class TravelPackageSummaryResponse(ResponseModel):
    """
    Lightweight shape for catalogue listing pages.
    Does NOT include full itinerary or inclusions — reduces payload size.
    """
    id:                  str
    title:               str
    slug:                str
    tagline:             str | None
    status:              PackageStatus
    destination_country: str
    destination_city:    str | None
    region:              str | None
    duration_days:       int
    duration_nights:     int
    base_price_usd:      Decimal
    price_per:           str
    is_featured:         bool
    flights_includable:  bool
    cover_image_url:     str | None = None

class TravelPackageResponse(AuditFieldsMixin):
    """Full package detail including all child entities."""
    title:               str
    slug:                str
    tagline:             str | None
    description:         str | None
    status:              PackageStatus
    destination_country: str
    destination_city:    str | None
    region:              str | None
    duration_days:       int
    duration_nights:     int
    base_price_usd:      Decimal
    price_per:           str
    min_participants:    int
    max_participants:    int | None
    flights_includable:  bool
    insurance_includable: bool
    is_featured:         bool
    # Nested
    highlights:    list[PackageHighlightResponse] = []
    inclusions:    list[PackageInclusionResponse] = []
    itinerary_days: list[PackageItineraryDayResponse] = []
    price_tiers:   list[PackagePriceTierResponse] = []
    # Media
    cover_image_url: str | None = None
    gallery:         list[PackageMediaResponse] = []
    # Analytics
    total_bookings: int = 0

PackageItineraryDayResponse.model_rebuild()
TravelPackageResponse.model_rebuild()
