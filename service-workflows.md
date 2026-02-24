# Service Workflows

This document outlines the exhaustive list of custom service (business logic) level class-based functions required for the full completion of the professional, enterprise-level web app backend. These functions orchestrate repositories, enforce business rules, and interface with external components.

## AuthService

- `register_client(payload)`: Handles registration, hashes password, creates preference records, triggers welcome email.
- `login(credentials)`: Validates credentials, checks active status, generates JWT/session, logs audit event.
- `verify_email(token)`: Confirms email verification tokens.
- `request_password_reset(email)`: Generates reset token and dispatches email via NotificationService.
- `admin_login(credentials)`: Strict login flow with potential MFA requirements for staff/admins.

## UserService & CompanyService

- `get_user_profile(user_id)`: Aggregates user data, active subscription status, and preferences.
- `update_preferences(user_id, payload)`: Validates and updates localization/notification settings.
- `process_referral(referrer_id, new_user_id)`: Credits the referrer's account upon successful conversion.
- `register_company(payload)`: Creates enterprise records and assigns the initial admin user.
- `manage_employees(company_id, admin_id, action, employee_data)`: Adds/removes company roster.

## SubscriptionService

- `subscribe_entity(user_id, company_id, plan_id, payment_details)`: Initiates a subscription, orchestrates PaymentService, limits checking.
- `check_booking_eligibility(user_id)`: Enforces business logic utilizing `UserSubscription` remaining counts and tier levels (Bronze, Silver, Gold).
- `renew_subscriptions()`: CRON job service to process recurring renewals and shift status arrays.
- `cancel_subscription(subscription_id)`: Handles soft-cancellations (retaining access until `current_period_end`).

## FlightService

- `search_flights(criteria)`: Interfaces with RapidAPI/Kayak to fetch available flights.
- `calculate_flight_markup(base_price)`: Interacts with `ServiceFeeRuleRepository` to apply dynamic domestic/intl upcharges.
- `hold_flight(pnr, passengers)`: Creates a pending `Booking` and `FlightBooking` with a strict time limit.
- `confirm_ticketing(booking_id)`: Moves booking to Ticketed after admin manual intervention/payment verification.

## PackageService

- `create_package(payload)`: Complex orchestration to save package details, inclusions, day-by-day itineraries, and media sequentially.
- `get_package_details(slug)`: Aggregates full package view including active pricing seasons and upcoming departures.
- `calculate_package_price(package_id, departure_id, occupancy_matrix)`: Resolves pricing based on the current season, adult/child split, and available capacity.

## BookingService (Orchestrator)

- `initiate_checkout(cart_payload, user_id)`: Generates the master `Booking` record, locks in pricing via `BookingLineItem` (Phase 2 ledger), and creates child passenger records.
- `cancel_booking(booking_id, user_id)`: Enforces cancellation policies, releases `PackageDeparture` capacity, orchestrates refunds.
- `approve_custom_itinerary(package_booking_id)`: Handles client/staff negotiations for customized group packages.

## Payment & InvoiceService

- `initialize_payment(booking_id, method)`: Sets up Stripe intents or issues Manual Transfer instructions.
- `verify_manual_payment(payment_id, admin_id)`: Staff workflow to confirm wire transfers/Zelle receipts, transitioning Booking status to Payment_Confirmed.
- `process_webhook_event(payload)`: Handles asynchronous provider callbacks (e.g., Stripe success/fail).
- `generate_invoice(booking_id/subscription_id)`: Compiles data, generates PDF via utility, saves URL to `Invoice` model.

## Platform Operations (Notification, Audit, Analytics)

- `NotificationService.dispatch_event(trigger_event, user_id, context)`: Loads DB template, injects context vars, sends email/SMS asynchronously.
- `AuditService.track(action, user, entity, changes)`: Secures immutable logs for admin actions (e.g., verifying payments).
- `AnalyticsService.generate_admin_dashboard(date_range)`: Aggregates flight volume, package sales, and revenue via `AnalyticsMetricRepository`.
