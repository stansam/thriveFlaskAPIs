# Thrive Travel Backend - Data Models Documentation

This document provides a comprehensive reference for the SQLAlchemy ORM models used in the Thrive Travel application.

## Core Models

### 1. `BaseModel` (`app/models/base.py`)

Abstract base class for all models.

- **Fields**:
  - `id` (UUID): Primary Key.
  - `created_at` (DateTime): Timestamp of declaration (UTC).
  - `updated_at` (DateTime): Timestamp of last update (UTC).
  - `deleted_at` (DateTime): Timestamp for soft deletion.
- **Best Practices**: Standardizes ID generation and audit timestamps. Implements Soft Delete pattern.

### 2. `User` (`app/models/user.py`)

Central entity representing a system user (Client, Admin, Staff).

- **Fields**:
  - `email` (String, Unique): User's login email. Indexed for fast lookup.
  - `password_hash` (String): Securely hashed password.
  - `role` (Enum: `UserRole`): RBAC role.
  - `subscription_tier` (Enum: `SubscriptionTier`): Usage level.
  - `referral_code` (String, Unique): For referral system.
  - `referrer_id` (FK): Self-referential link to the user who referred this user.
- **Relationships**:
  - `company`: Corporate parent (if applicable).
  - `preferences`: One-to-One with `UserPreference`.
  - `bookings`, `payments`, `notifications`: One-to-Many.
- **Security**: PII (Phone, Email) should be treated with care.

### 3. `UserPreference` (`app/models/user_preference.py`)

Stores customizable settings for a user.

- **Fields**:
  - `currency`, `language`, `timezone`: Localization settings.
  - `marketing_opt_in`, `email_updates`: Privacy & Notification toggles.

### 4. `Company` (`app/models/company.py`)

Represents a corporate entity for B2B features.

- **Fields**:
  - `subscription_tier`: Corporate subscription level.
  - `subscription_status`: Status of the company's account.
- **Relationships**:
  - `employees`: List of Users belonging to this company.

### 5. `AuditLog` (`app/models/audit_log.py`)

Immutable record of system actions.

- **Fields**:
  - `action`: String (Should be Enum).
  - `entity_type`: String (Should be Enum).
  - `changes`: JSON storing before/after state.
- **Best Practices**: Critical for security and debugging.

## Booking & Travel Models

### 6. `Booking` (`app/models/booking.py`)

**Polymorphic Parent** for all reservation types.

- **Fields**:
  - `reference_code` (String, Unique): Human-readable booking ref (e.g., "THRIVE-A1B2").
  - `status` (Enum: `BookingStatus`): Lifecycle state.
  - `booking_type` (Enum: `BookingType`): Discriminator (Flight, Package, etc.).
  - `total_amount`, `currency`: Financials.
- **Relationships**:
  - `passengers`: List of travelers.
  - `flight_booking` / `package_booking`: Child details.

### 7. `Passenger` (`app/models/passenger.py`)

Traveler details attached to a booking.

- **Fields**:
  - `passport_number`: Sensitive PII.
  - `date_of_birth`: Sensitive PII.

### 8. `FlightBooking` & `Flight` (`app/models/flight_booking.py`)

- `FlightBooking`: Container for a flight reservation (PNR).
- `Flight`: Specific segment mechanics (Carrier, Flight Number, Times).
  - _Note_: Stores a snapshot of flight data at time of booking.

### 9. `Package` (`app/models/package.py`)

Catalog item for a Tour/Package.

- **Fields**:
  - `slug`: URL-friendly identifier.
  - `base_price`: Starting cost.
- **Relationships**:
  - `itinerary`: Daily schedule (`PackageItinerary`).
  - `inclusions`: What is covered.

### 10. `PackageBooking` (`app/models/package_booking.py`)

Instance of a user booking a package.

- **Fields**:
  - `start_date`, `end_date`: Travel window.
  - `custom_itinerary`: Link to ad-hoc customizations.

## Finance & Operations

### 11. `Payment` (`app/models/payment.py`)

Transactional record.

- **Fields**:
  - `status` (Enum: `PaymentStatus`).
  - `transaction_id`: External gateway ref (Stripe/PayPal).

### 12. `Invoice` (`app/models/payment.py`)

Billing document.

- **Fields**:
  - `invoice_number`: Unique sequential ID.
  - `status`: Currently string, should be Enum.

### 13. `Notification` (`app/models/notification.py`)

System alerts.

- **Fields**:
  - `type` (Enum: `NotificationType`).
  - `priority`: Currently string, should be Enum.

## Recommended Improvements (Gap Analysis)

The following changes are recommended to enforce strict typing and data integrity:

1.  **Enums**:
    - Create `AuditAction` Enum for `AuditLog.action`.
    - Create `EntityType` Enum for `AuditLog.entity_type`.
    - Create `SubscriptionStatus` Enum for `Company` and `UserSubscription`.
    - Create `NotificationPriority` Enum.
    - Create `ActivityType` Enum for `PackageItinerary`.
    - Create `ServiceType` Enum for `CustomItineraryItem`.
    - Create `InvoiceStatus` Enum.
    - Create `Gender` Enum for `Passenger`.

2.  **Indexing**:
    - Ensure `booking_id` in child tables is indexed (Foreign Keys usually are, but explicit check matches good practice).

3.  **Methods**:
    - Add `__repr__` methods to all models for easier debugging in Flask Shell.
