# Flight Search & Booking System Analysis Report

## 1. Executive Summary

The current Thrive Backend is a robust skeleton built with Flask, SQLAlchemy, and a Service/Repository pattern. Authentication (`app/auth`) and User Management (`app/repository/user`) are fully implemented and tested. However, the core business domain—Flight Search, Booking, and Admin/Client dashboards—exists primarily as skeletons or mock implementations. This report outlines the strategy to implementations a production-grade flight booking system by integrating the Kayak-style Flight Search API.

## 2. Codebase State Analysis

### 2.1 Existing Infrastructure (Ready)

- **Authentication**: Robust JWT/Session-based auth with Google OAuth support (`app/auth`).
- **Database Models**: Comprehensive schema in `app/models` covering `User`, `Booking`, `FlightBooking`, `Passenger`, `Payment`, `Invoice`, and `AuditLog`.
- **Base Services**: `UserService`, `NotificationService`, and `EmailService` are implemented and operational.
- **Testing**: Good test fixtures (`conftest.py`) and specific tests for Auth and mock Services.

### 2.2 Gaps & Missing Logic (To Build)

- **Flight Service**: Currently a mock. Needs integration with the external generic Flight Search API.
- **Booking Service**: Basic CRUD exists but lacks the complex state machine for flight booking (Validation -> Hold -> Payment -> Ticket).
- **Finance Service**: Payment processing is mocked. Needs real integration (e.g., Stripe) and proper fee/invoice logic.
- **Blueprints**: `app/main`, `app/client`, and `app/admin` are empty shells. Routes need to be defined.
- **Schemas**: Validations for generic search, booking, and passenger details are missing.

## 3. Flight API Integration Strategy

### 3.1 Search Workflow

**Endpoint**: `POST /api/flight/search`

- **Input**: Maps to `flightsAPIOverview.md` parameters (origin, destination, date, passengers).
- **Processing**: Calls External API (RapidAPI).
- **Response**: Normalizes `flightSearchResp.json` into a frontend-friendly format. The backend should cache the `results` and `legs` to minimize downstream API calls.

### 3.2 Details & Selection

**Endpoint**: `GET /api/flight/details/{id}`

- **Logic**: Retrieves full details using `flightDetailsResp.json` structure.
- **Data Mapping**:
  - `flights` array maps to `Flight` model segments.
  - `query_info` validates consistency.

## 4. Booking Workflow Analysis

### Step 1: Search & Select

User queries flights. Backend returns normalized results. User selects a specific `bookingOption` (Itinerary).

### Step 2: Passenger Details (Draft Booking)

**Endpoint**: `POST /api/booking/initiate`

- **Action**: detailed validation of selected flight price and availability (Live Check).
- **Data**: Creates a `Booking` record with status `PENDING` and a linked `FlightBooking` with `pnr_reference` (temporary).
- **Models**: `Booking`, `FlightBooking`, `Passenger` records created.

### Step 3: Payment

**Endpoint**: `POST /api/booking/{id}/payment`

- **Action**: Processes payment via `FinanceService`.
- **Validation**: Checks if booking is still valid/held.
- **Result**: transitions `BookingStatus` to `CONFIRMED`. Creates `Payment` and `Invoice` records.

### Step 4: Ticketing & Notification

- **Action**: Async task triggers after payment.
- **Logic**: Issues official e-ticket, generates PDF invoice, sends specific Email/SMS notifications.
- **Models**: Updates `FlightBooking` with `eticket_number`.

## 5. Data Modeling & Mapping

| External API Entity           | Thrive Model                | Notes                                          |
| ----------------------------- | --------------------------- | ---------------------------------------------- |
| `flightSearchResp.results`    | `FlightBooking` (Potential) | Transient during search; persisted on booking. |
| `flightSearchResp.legs`       | `Flight`                    | A leg may contain multiple segments (stops).   |
| `flightSearchResp.segments`   | `Flight`                    | Direct mapping to `Flight` table fields.       |
| `userSearchParams.passengers` | `Passenger`                 | Mapped during booking creation.                |
| `price.total`                 | `Booking.total_amount`      | Includes base fare + taxes + service fees.     |

## 6. Recommendations

1.  **Implement `FlightService` Adapter**: Create a dedicated adapter pattern to handle External API calls, allowing easy switching of providers (Amadeus/Sabre/Kayak).
2.  **State Machine for Bookings**: Use a library or strict pattern to manage transitions (`PENDING` -> `AWAITING_PAYMENT` -> `CONFIRMED` -> `TICKETED`).
3.  **Frontend-Backend Contract**: Define strict Pydantic/Marshmallow schemas for the search response to decouple the frontend from the raw External API structure.
4.  **Async Processing**: Use the existing Celery setup for "Ticketing" and "Emailing" to ensure payment API response is fast.
