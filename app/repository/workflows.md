# Backend Workflows & Service Architecture

This document outlines the design and implementation guidelines for the Thrive Travel backend services.

## Service Architecture

We follow a **Repository/Service Pattern** with a focus on **Single Responsibility Operations**.

### Directory Structure

All services reside in `app/repository/<domain>/`.

```
app/repository/
└── <domain>/                # e.g., user, booking, finance
    ├── __init__.py
    ├── services.py          # Facade class exposing domain operations
    ├── exceptions.py        # Domain-specific exceptions
    └── ops/                 # Individual operation classes
        ├── __init__.py
        ├── create.py        # Logic for creation
        ├── get.py           # Logic for retrieval
        ├── update.py        # Logic for updates
        ├── delete.py        # Logic for deletion
        └── [specific_op].py # Domain-specific logic (e.g., issue_ticket.py)
```

### Coding Standards

1.  **Service Facade**: The `Service` class (e.g., `BookingService`) initializes with a `db` session and provides methods that instantiate and call `execute()` on Operation classes.
2.  **Operation Classes**: Each class in `ops/` should have a single responsibility and an `execute()` method.
3.  **Error Handling**:
    - Catch `SQLAlchemyError` and wrap it in a custom `DatabaseError`.
    - Raise domain-specific exceptions (e.g., `BookingNotFound`, `PaymentFailed`) for logic errors.
    - Never expose raw database exceptions to the controller layer.
4.  **Type Hinting**: Use strict type hints for all method arguments and return values.
5.  **Validation**: Validate inputs at the Service/Operation layer before interacting with the database.

---

## Contextualized Workflows

### 1. User Management (`app/repository/user`)

_Already implemented (Reference)_

- **Registration**: Create User -> Generate Verification Token -> Send Email.
- **Authentication**: Login -> Issue JWT.
- **Profile**: Update details, Manage Preferences.

### 2. Booking System (`app/repository/booking`)

Handles the lifecycle of a reservation.

- **Create Booking**: Initialize a booking in `PENDING` state. Validates availability.
- **Add Passengers**: Link travelers to the booking.
- **Confirm Booking**: Transition to `CONFIRMED` after successful payment.
- **Cancel Booking**: Handle cancellations and trigger refund logic.
- **Get User Bookings**: Retrieve history for a specific user.

### 3. Flight Management (`app/repository/flight`)

Manages flight data and external integrations (mocked for now).

- **Search Flights**: Query available flights based on criteria.
- **Get Flight Details**: Retrieve metadata for a specific flight.
- **Reserve Seat**: Lock a seat for a booking.

### 4. Package Management (`app/repository/package`)

CMS-like functionality for travel packages.

- **Create Package**: Admin adds a new tour.
- **Update Package**: Modify itinerary or pricing.
- **Search Packages**: Filter by destination, price, duration.
- **Check Availability**: Validate dates (if applicable).

### 5. Finance & Payments (`app/repository/finance`)

Handles money movement and records.

- **Process Payment**: Record a transaction (integrates with Stripe/PayPal).
- **Generate Invoice**: Create a PDF invoice for a confirmed booking.
- **Refund Payment**: Process full or partial refunds.
- **Calculate Fees**: Apply service fee rules to a booking total.

### 6. Notifications (`app/repository/notification`)

Centralized communication handler.

- **Send Notification**: Dispatch Email/SMS/In-App alert.
- **Mark Read**: Update status of in-app notifications.
- **Get User Notifications**: Fetch alert history.

## Security Best Practices

1.  **Input Sanitation**: Rely on Pydantic schemas (in API layer) and ORM sanitization.
2.  **Authorization**: Services should assume the caller has permission (Controller layer handles RBAC), but critical checks (e.g., "User owns this booking") can be reinforced here.
3.  **Audit Logging**: Critical actions (Payment, Cancellation, Ban) must trigger an `AuditLog` entry.
4.  **Transaction Management**: Operations should manage their own atomic transactions (`commit`/`rollback`).

### 7. Email Service (`app/repository/email`)

Handles the actual dispatch of emails via SMTP or API (e.g., SendGrid/AWS SES).

- **Send Email**: generic method to send html/text emails.
- **Send Template Email**: Send email using a stored template (e.g., `NotificationTemplate`).
- **Verify Email Address**: Check if an email is valid/deliverable (optional integration).
