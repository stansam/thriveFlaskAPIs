# dtos/common.py
"""
Shared Pydantic v2 base classes used across all DTOs.

Design rules
------------
1.  All Response models inherit `AuditFieldsMixin` which carries the
    four audit columns (id, created_at, updated_at, created_by_id,
    updated_by_id) so every response automatically includes them.

2.  All Request models use `model_config = ConfigDict(str_strip_whitespace=True)`
    so user input is always trimmed before validation.

3.  All monetary Decimal fields are serialised as strings in JSON output
    (`json_encoders={Decimal: str}`) to prevent IEEE-754 precision loss
    across languages.  Clients must treat them as arbitrary-precision strings.

4.  `PaginationMeta` wraps every paginated list endpoint response.

5.  `ErrorResponse` is the standard error envelope returned by all
    4xx / 5xx route handlers.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_serializer

T = TypeVar("T")

# Base configs
class StrictRequestModel(BaseModel):
    """
    Base for all inbound request bodies.
    - Strips whitespace from all string inputs.
    - Forbids extra fields (no silent field ignoring).
    - Validates assignment so mutated instances stay valid.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
    )

class ResponseModel(BaseModel):
    """
    Base for all outbound response shapes.
    - Reads from ORM attributes (from_attributes=True).
    - Serialises Decimal as str to avoid float precision loss.
    - Serialises datetime as ISO-8601 UTC string.
    - Does NOT forbid extra fields (ORM objects often carry extra attrs).
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        # use_enum_values=True,
    )

    @model_serializer(mode="wrap")
    def _serialize(self, handler: Any, info: Any) -> Any:
        # Standard dump
        data = handler(self)
        
        # If serialization mode is JSON, apply custom encoders
        if info.mode == "json":
            for key, value in data.items():
                if isinstance(value, Decimal):
                    data[key] = str(value)
                elif isinstance(value, datetime):
                    data[key] = value.isoformat()
        return data

# Audit fields mixin
class AuditFieldsMixin(ResponseModel):
    """
    Injected into every Response model.
    Carries the four standard audit columns.
    """
    id: str
    created_at: datetime
    updated_at: datetime
    created_by_id: str | None = None
    updated_by_id: str | None = None

# Pagination
class PaginationMeta(ResponseModel):
    """Pagination envelope metadata."""
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedResponse(ResponseModel, Generic[T]):
    """
    Generic paginated list response.
    Usage: PaginatedResponse[BookingResponse]
    """
    items: list[T]
    pagination: PaginationMeta

# Error response
class FieldError(ResponseModel):
    field: str
    message: str

class ErrorResponse(ResponseModel):
    """Standard error envelope for all 4xx / 5xx responses."""
    error: str
    message: str
    details: list[FieldError] | None = None
    request_id: str | None = None
    code: int = 400

# Success response (for actions that return no body)
class SuccessResponse(ResponseModel):
    success: bool = True
    message: str = "Operation completed successfully."
    code: int = 200
