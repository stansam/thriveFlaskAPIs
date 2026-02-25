# TRUE Backend Completion Plan

_Based on intensive codebase analysis, this is the definitive, step-by-step technical roadmap to un-stub, secure, and productionize the Thrive backend._

## Phase 1: Securing Data Access & Integrity (The Foundation)

_Objective: Solidify how the application reads, writes, and limits data to prevent database lockups and financial calculation errors._

1. **Implement Aggressive Pagination**
   - **Target:** `app/admin/routes/companies.py`, `app/admin/routes/bookings.py`, `app/admin/routes/audit.py`
   - **Action:** Replace `.all()` calls with native SQLAlchemy `.paginate(page=X, per_page=Y)` to protect memory limits during bulk fetches.
2. **Finalize Financial & Subscription Mathematics**
   - **Target:** `app/services/subscription/service.py`
   - **Action:** Build mathematical prorated differentials comparing the unused days of an old plan against the daily burn rate of the new plan when an Admin triggers an upgrade.
   - **Target:** `app/admin/routes/dashboard.py`
   - **Action:** Wire the dashboard explicitly to `repositories.analytics.calculate_total_revenue_by_period()` to return live DB SUM() aggregations rather than the `$125,000` mock string.
3. **Enforce Absolute Database Limits**
   - **Target:** `app/services/company/utils.py`
   - **Action:** Delete the hard-coded `seat_limit = 50`. Force the logic to physically query `SubscriptionPlan.fee_waiver_rules` or `booking_limit_count` dynamically.
4. **Refine Soft-Delete Architecture**
   - **Target:** `app/repository/user/repository.py`
   - **Action:** Ensure all `.query` blocks natively filter out `is_active=False` users so soft-deleted targets never appear in admin listings.

## Phase 2: Closing the Transactional Loop (Business Logic)

_Objective: Connect the user actions natively to the real world (APIs, Emails, and States)._

1. **GDS Live API Integration**
   - **Target:** `app/services/flight/service.py`
   - **Action:** Strip the mock dictionaries. Implement the physical `requests` adapter to RapidAPI/Kayak, parse the JSON, and map it cleanly to `FlightBookingDTO`.
   - **Reference:** SLOWLY AND WITH SENIOR DEVELOPER's CRITICAL THINKING, CARE AND FORWARD PLANNING: carefully and critically analyse the Flight search API endpoint's response structure from the JSON file (`flightSearchResp.json` and it's expected request params structure is crafted in `app/repository1/flight/requestDTO/__init__.py` ) craft the relevant ENUMS, DTOs/Schemas for the API adapter's search_flights method(Also crafted was the expected search flight API response DTOs and ENUMS mapped from the JSON file, the file is located in `app/repository1/flight/structure/__init__.py`). Similarly the API's Flight details endpoint response structure is in `flightDetailsResp.json` and it's expected request params are `flight_number`: string, `airline_id`: string and optionally `return_date`: string, craft the relevant DTOs/Schemas for the adapter's flight_details method. Also similarly analyse the API's airport search endpoint's format in `airport-search.md` and craft the relevant DTOs/Schemas and Enums for the adapter's search_airports method. Configure strict caching considering the API's rate limits and the need for fresh data, but consider unique caching standards, for example airport search might be stored for a longer period of time. REITERATE TO ENSURE FULL UNDERSTANDING OF THE API'S REQUEST AND RESPONSE STRUCTURES BEFORE CRAFTING THE DTOs/SCHEMAS AND ENUMS AND VERIFY DEPENDENT APP WORKFLOWS AND INTEGRATIONS SMOOTHLY AND SECURELY. This part is important as it forms the backbone of the flight search and booking functionality so treat it with utter caution and dexterity. First when implementing branch at this point and create a seperate implementation plan for designing, creating, intergrating and verifying the COMPLETE API adapter into the existing codebase, break it into manageable steps but ensure completion.The API provides only these three endpoints, for instance the search flights api response includes providers and payment urls which will be used to book the flight and get the ticket by the admin after client successfully books the flight on this website, makes payment and is successfully confirmed by the admin. Also the flight-details endpoint can be used to track the flight live. The search-airports endpoint will be used to populate the frontend's departure/origin fields in a flight search form.

2. **Physical Email Dispatch**
   - **Target:** `app/services/notification/service.py` and `app/services/auth/service.py`
   - **Action:** Remove the `print("Mock sending email")` statements. Wire Python's `smtplib` or SendGrid adapter, binding it to the pre-built `app/templates/email/` MJML models.
3. **Stateless Password & Verification Tokens**
   - **Target:** `app/auth/routes/forgot_password.py`, `reset_password.py`
   - **Action:** Utilize `itsdangerous.URLSafeTimedSerializer` to generate cryptographically signed tokens bearing strict timestamps, dropping reliance on raw database strings.
4. **OAuth Exchange Finalization**
   - **Target:** `app/auth/routes/google.py`
   - **Action:** Execute the physical HTTP exchange trading the frontend `code` for the native Google access token and user identity block.
5. **Booking State Machine Completions**
   - **Target:** `app/admin/routes/bookings.py`
   - **Action:** Ensure that cancelling a booking natively releases locked inventory logic and pushes a state-change ping to the `audit_log`.

## Phase 3: Asynchronous Scaffolding & Scale

_Objective: Shift heavy I/O tasks out of the main execution threads to preserve API speed._

1. **Activate Celery Fabric**
   - **Target:** `celery_worker.py`, `app/utils/celery_utils.py`
   - **Action:** Ensure Redis is bound and the worker threads are capable of receiving tasks dynamically.
2. **Deferred Workloads**
   - **Action:** Refactor all Notification endpoints (`send_welcome_email`, `send_reset_password`) to utilize `.delay()`, throwing the SMTP blocking time into the background worker.
   - **Action:** For large CSV package uploads (`app/admin/routes/packages.py`), bind the DB insertion loop to a background task that emails the Admin upon successful parsing.
3. **Real-time Telemetry (Sockets)**
   - **Target:** `app/main/routes/flights.py`, `app/sockets/`
   - **Action:** Implement Flask-SocketIO `emit()` triggers on high-value actions (e.g., flight searches, verified payments) to push live updates to the frontend natively.

## Phase 4: Security & Audit Hardening

_Objective: Lock down the completed system against unauthorized escalations._

1. **Action Boundaries**
   - **Target:** `app/services/payment/service.py`
   - **Action:** Safely write specific, immutable `AuditLog` rows indicating EXACTLY which `admin_user_id` executed a specific payment verification bypass or refund.
2. **Password Strictness**
   - **Action:** Enhance `RegisterSchema` validation (`app/auth/schemas/register.py`) forcing complexity (1 Upper, 1 Special, etc.).
3. **PNR Formatting**
   - **Target:** `app/repository/booking/utils.py`
   - **Action:** Guarantee the booking reference generator produces standard 6-character Airline PNR structures (Alphanumeric, collision-tested).
