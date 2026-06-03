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

from app.dto.common import PaginationMeta, AuditFieldsMixin
from app.dto.user import (
    UserCreateRequest, UserUpdateRequest, UserResponse, AdminUserResponse,
    PasswordChangeRequest, PasswordResetRequest, LoginRequest,
    MFASetupResponse, ForgotPasswordResponse, UserListResult
)
from app.dto.client import (
    ClientCreateRequest, ClientUpdateRequest, ClientResponse, ClientSummaryResponse
)
from app.dto.corporate import (
    CorporateAccountCreateRequest, CorporateAccountUpdateRequest, CorporateAccountResponse,
    CorporateSubscriptionCreateRequest, CorporateSubscriptionUpdateRequest,
    CorporateSubscriptionResponse,
)
from app.dto.package import (
    TravelPackageCreateRequest, TravelPackageUpdateRequest, TravelPackageResponse,
    TravelPackageSummaryResponse,
)
from app.dto.package_items import (
    PackageHighlightCreateRequest, PackageHighlightResponse,
    PackageInclusionCreateRequest, PackageInclusionResponse,
    PackageItineraryDayCreateRequest, PackageItineraryDayUpdateRequest,
    PackageItineraryDayResponse,
    PackagePriceTierCreateRequest, PackagePriceTierUpdateRequest, PackagePriceTierResponse,
)
from app.dto.booking import (
    BookingSummaryResponse, BookingStatusTransitionRequest,
)
from app.dto.flight_booking import (
    FlightBookingCreateRequest, FlightBookingUpdateRequest, FlightBookingResponse,
    FlightSegmentCreateRequest, FlightSegmentResponse,
)
from app.dto.hotel_booking import (
    HotelBookingCreateRequest, HotelBookingUpdateRequest, HotelBookingResponse,
)
from app.dto.car_booking import (
    CarBookingCreateRequest, CarBookingUpdateRequest, CarBookingResponse,
)
from app.dto.package_booking import (
    PackageBookingCreateRequest, PackageBookingUpdateRequest, PackageBookingResponse,
)
from app.dto.booking_passenger import (
    BookingPassengerCreateRequest, BookingPassengerResponse,
)
from app.dto.payment import (
    PaymentCreateRequest, PaymentUpdateRequest, PaymentResponse, PaymentConfirmRequest,
)
from app.dto.fee import (
    ServiceFeeScheduleCreateRequest, ServiceFeeScheduleResponse,
    ServiceFeeCreateRequest, ServiceFeeResponse,
    ServiceFeeSnapshotResponse,
)
from app.dto.media import MediaAssetResponse, MediaAssetUploadRequest, PackageMediaResponse
from app.dto.preference import (
    UserPreferenceUpdateRequest, UserPreferenceResponse,
    ClientPreferenceUpdateRequest, ClientPreferenceResponse,
)
from app.dto.notification import (
    NotificationTemplateCreateRequest, NotificationTemplateUpdateRequest,
    NotificationTemplateResponse,
    NotificationResponse, NotificationListResponse,
    NotificationDeliveryResponse,
)
from app.dto.referral import ReferralResponse, ReferralCreateRequest
from app.dto.loyalty import LoyaltyLedgerEntryResponse, LoyaltyBalanceResponse
from app.dto.audit import AuditLogResponse
