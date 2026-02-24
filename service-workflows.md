# Service Workflows

This document outlines an exhaustive list of custom service-level class-based functions required to orchestrate business logic, handle transactions across multiple repositories, and integrate with external APIs for the enterprise backend.

## 1. AuthService

- `login_user(credentials: dict) -> Tuple[str, User]` - Authenticates a user and generates JWT tokens.
- `register_user(data: dict) -> User` - Handles user creation, password hashing, and triggers welcome email verification.
- `verify_email(token: str) -> bool` - Verifies a user's email address using a secure token.
- `request_password_reset(email: str) -> bool` - Generates a password reset token and dispatches an email.
- `reset_password(token: str, new_password: str) -> bool` - Validates the token and updates the user's password.

## 2. UserService

- `get_profile(user_id: str) -> dict` - Assembles user details, preferences, and active subscription status.
- `update_profile(user_id: str, data: dict) -> User` - Validates and applies updates to user demographics.
- `update_preferences(user_id: str, prefs: dict) -> UserPreference` - Manages notification and localization settings.
- `delete_account(user_id: str) -> bool` - Orchestrates the soft-deletion of a user and anonymization of sensitive PII data.

## 3. CompanyService

- `onboard_company(data: dict) -> Company` - Creates a new corporate entity and assigns an initial admin user.
- `manage_employees(company_id: str, admin_id: str, action: str, user_data: dict) -> User` - Handles adding, removing, or updating employees within a company grouping.

## 4. SubscriptionService

- `subscribe_to_plan(entity_id: str, entity_type: EntityType, plan_name: str, payment_method: dict) -> UserSubscription` - Handles billing setup, invoice generation, and activates a new subscription tier.
- `upgrade_plan(subscription_id: str, new_plan_name: str) -> UserSubscription` - Calculates prorated charges and alters the subscription plan.
- `cancel_subscription(subscription_id: str) -> bool` - Sets the subscription to expire at the end of the current billing cycle.
- `check_booking_eligibility(user_id: str) -> bool` - Orchestrates logic to verify if a user's subscription permits further bookings this cycle.

## 5. FlightService

- `search_flights(params: FlightSearchRequestDTO) -> SearchFlightResponseDTO` - Interfaces with the Kayak adapter, normalizes data, and applies business rules.
- `get_flight_details(search_id: str, flight_id: str) -> dict` - Retrieves specific metadata and pricing for a selected flight.
- `book_flight(user_id: str, flight_data: dict, passengers: List[dict], payment_intent: dict) -> FlightBooking` - Orchestrates Booking creation, Passenger insertion, LineItem generation (base + service fees), and delegates payment processing.
- `cancel_flight_booking(booking_id: str, user_id: str) -> bool` - Reverses a transaction, triggers audits, and requests airline cancellation APIs.

## 6. PackageService

- `explore_packages(filters: dict) -> List[Package]` - Handles aggregation of packages, media, and pricing.
- `get_package_details(slug: str) -> dict` - Retrieves the full itinerary, inclusions, and valid departures for a package.
- `book_package(user_id: str, package_id: str, departure_id: str, passengers: List[dict], custom_requests: str) -> PackageBooking` - Validates departure capacity, attempts optimistic locking decrement via Repository, calculates total pricing with LineItems, and attempts payment.
- `customize_itinerary(booking_id: str, custom_items: List[dict]) -> CustomItinerary` - Approves and links custom itinerary activities to a package booking.

## 7. PaymentService

- `process_payment(invoice_id: str, payment_method: dict) -> Payment` - Interfaces with external payment gateways (e.g., Stripe) to capture funds.
- `handle_webhook(payload: dict, signature: str) -> bool` - Securely parses async gateway webhooks to finalize pending payments or flag failures.
- `generate_invoice(user_id: str, amount: float, description: str, linked_entity_type: str, linked_entity_id: str) -> Invoice` - Generates PDF invoices and database records for successful transactions.
- `process_refund(payment_id: str, amount: float, reason: str) -> bool` - Instructs the gateway to reverse a charge and audits the action.

## 8. NotificationService

- `dispatch_notification(user_id: str, trigger_event: str, context: dict) -> bool` - Fetches the appropriate `NotificationTemplate`, renders variables using Jinja, and sends in-app/email alerts.
- `send_email(to_email: str, subject: str, body_html: str) -> bool` - Low-level wrapper around the SMTP/SES email provider.

## 9. AnalyticsService

- `track_event(metric_name: str, category: str, value: float = 0.0) -> None` - Asynchronously bumps counter metrics for traffic, conversion, and usage.
- `generate_dashboard_report(start_date: date, end_date: date) -> dict` - Aggregates time-series data from `AnalyticsMetric` models for admin dashboards.

## 10. AuditService

- `record_critical_action(user_id: str, action: AuditAction, entity_type: EntityType, entity_id: str, diff: dict) -> None` - Wrapper used by decorators or critical service flows to enforce compliance logging.
