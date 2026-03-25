# dtos/__init__.py
"""
Data Transfer Objects (DTOs) for the Thrive Global Travel & Tours API.

Technology: Pydantic v2 (model_config, field validators, model_validator).

Convention
----------
Every domain has three shapes:
  *CreateRequest   — inbound POST body; required fields, strict validation
  *UpdateRequest   — inbound PATCH body; all fields Optional
  *Response        — outbound JSON shape; includes computed / joined fields
  *ListResponse    — paginated envelope wrapping list[*Response]

Shared DTOs
-----------
  PaginationMeta   — page / total / has_next metadata
  AuditFieldsMixin — created_at, updated_at, created_by_id, updated_by_id

Naming:
  All monetary amounts are Decimal; serialised as strings in JSON to
  avoid IEEE-754 floating-point precision loss.
  All datetimes are UTC ISO-8601 strings in responses.
  All UUIDs are plain strings (str) — no uuid.UUID type overhead.
"""

from .common import PaginationMeta, AuditFieldsMixin
from .user import (
    UserCreateRequest, UserUpdateRequest, UserResponse,
    PasswordChangeRequest, PasswordResetRequest, LoginRequest,
    MFASetupResponse, ForgotPasswordResponse,
)
from .client import (
    ClientCreateRequest, ClientUpdateRequest, ClientResponse,
)
from .corporate import (
    CorporateAccountCreateRequest, CorporateAccountUpdateRequest, CorporateAccountResponse,
    CorporateSubscriptionCreateRequest, CorporateSubscriptionUpdateRequest,
    CorporateSubscriptionResponse,
)
from .package import (
    TravelPackageCreateRequest, TravelPackageUpdateRequest, TravelPackageResponse,
    TravelPackageSummaryResponse,
)
from .package_items import (
    PackageHighlightCreateRequest, PackageHighlightResponse,
    PackageInclusionCreateRequest, PackageInclusionResponse,
    PackageItineraryDayCreateRequest, PackageItineraryDayUpdateRequest,
    PackageItineraryDayResponse,
    PackagePriceTierCreateRequest, PackagePriceTierUpdateRequest, PackagePriceTierResponse,
)
from .booking import (
    BookingCreateRequest, BookingUpdateRequest, BookingResponse,
    BookingSummaryResponse, BookingStatusTransitionRequest,
)
from .flight_booking import (
    FlightBookingCreateRequest, FlightBookingUpdateRequest, FlightBookingResponse,
    FlightSegmentCreateRequest, FlightSegmentResponse,
)
from .hotel_booking import (
    HotelBookingCreateRequest, HotelBookingUpdateRequest, HotelBookingResponse,
)
from .car_booking import (
    CarBookingCreateRequest, CarBookingUpdateRequest, CarBookingResponse,
)
from .package_booking import (
    PackageBookingCreateRequest, PackageBookingUpdateRequest, PackageBookingResponse,
)
from .booking_passenger import (
    BookingPassengerCreateRequest, BookingPassengerResponse,
)
from .payment import (
    PaymentCreateRequest, PaymentUpdateRequest, PaymentResponse, PaymentConfirmRequest,
)
from .fee import (
    ServiceFeeScheduleCreateRequest, ServiceFeeScheduleResponse,
    ServiceFeeCreateRequest, ServiceFeeResponse,
    ServiceFeeSnapshotResponse,
)
from .media import MediaAssetResponse, MediaAssetUploadRequest, PackageMediaResponse
from .preference import (
    UserPreferenceUpdateRequest, UserPreferenceResponse,
    ClientPreferenceUpdateRequest, ClientPreferenceResponse,
)
from .notification import (
    NotificationTemplateCreateRequest, NotificationTemplateUpdateRequest,
    NotificationTemplateResponse,
    NotificationResponse, NotificationListResponse,
    NotificationDeliveryResponse,
)
from .referral import ReferralResponse, ReferralCreateRequest
from .loyalty import LoyaltyLedgerEntryResponse, LoyaltyBalanceResponse
from .audit import AuditLogResponse
