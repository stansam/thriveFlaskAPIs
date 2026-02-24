# Database Repository Workflows

This document outlines an exhaustive list of custom repository-level class-based functions required to manage the data access layer for the enterprise backend. These repositories abstract SQLAlchemy queries, ensuring the service layer remains unaware of direct database interactions.

## 1. UserRepository

- `find_by_email(email: str) -> Optional[User]` - Retrieves a user by their email address.
- `find_by_company(company_id: str) -> List[User]` - Retrieves all users associated with a specific company.
- `get_user_with_preferences(user_id: str) -> Optional[User]` - Fetches a user and eagerly loads their `UserPreference` relationship.
- `count_active_users_by_role(role: UserRole) -> int` - Aggregates the total number of active users for a specific role.
- `soft_delete_user(user_id: str) -> bool` - Marks a user as deleted without physically removing the record.
- `restore_user(user_id: str) -> bool` - Restores a soft-deleted user.

## 2. CompanyRepository

- `find_by_tax_id(tax_id: str) -> Optional[Company]` - Retrieves a company by its unique tax ID.
- `get_company_with_employees(company_id: str) -> Optional[Company]` - Fetches a company and eagerly loads all associated users.
- `get_companies_by_status(is_active: bool) -> List[Company]` - Retrieves a list of companies based on their active status.
- `update_company_details(company_id: str, data: dict) -> Company` - Updates specific fields of a company record.

## 3. SubscriptionRepository

- `get_active_subscription_for_user(user_id: str) -> Optional[UserSubscription]` - Retrieves the currently active subscription for a specific user.
- `get_active_subscription_for_company(company_id: str) -> Optional[UserSubscription]` - Retrieves the currently active subscription for a company.
- `get_subscription_plan_by_name(name: str) -> Optional[SubscriptionPlan]` - Fetches a subscription plan by its name (e.g., "Enterprise").
- `list_expiring_subscriptions(days_until_expiry: int) -> List[UserSubscription]` - Queries subscriptions that are set to expire within a specific number of days.
- `update_usage_count(subscription_id: str, increment_by: int) -> UserSubscription` - Atomically increments the `bookings_used_this_period` counter.

## 4. BookingRepository

- `find_by_reference(reference_number: str) -> Optional[Booking]` - Retrieves a booking using its unique, customer-facing reference number.
- `get_user_bookings_history(user_id: str, limit: int, offset: int) -> List[Booking]` - Paginates a user's chronological booking history.
- `get_booking_with_line_items(booking_id: str) -> Optional[Booking]` - Fetches a booking and eagerly loads its immutable `BookingLineItem` ledger.
- `get_bookings_by_status(status: BookingStatus) -> List[Booking]` - Retrieves all bookings matching a specific status (e.g., PENDING, CONFIRMED).
- `update_booking_status(booking_id: str, new_status: BookingStatus) -> Booking` - Updates the status of a booking.
- `calculate_total_revenue_by_period(start_date: date, end_date: date) -> float` - Aggregates total revenue from confirmed bookings within a timeframe.

## 5. FlightBookingRepository

- `get_flight_booking_with_segments(booking_id: str) -> Optional[FlightBooking]` - Retrieves a flight booking and its associated `Flight` segments.
- `find_by_pnr(pnr_reference: str) -> Optional[FlightBooking]` - Retrieves a flight booking using the airline PNR reference.
- `update_eticket_info(booking_id: str, eticket_number: str, ticket_url: str) -> FlightBooking` - Updates ticketing details after fulfillment.

## 6. PackageRepository

- `search_packages(filters: dict, limit: int, offset: int) -> List[Package]` - Performs a complex search using filters (country, city, duration, highlights).
- `get_featured_packages(limit: int) -> List[Package]` - Retrieves a list of active packages flagged as featured.
- `get_package_with_full_details(package_id: str) -> Optional[Package]` - Eagerly loads itineraries, inclusions, media, and pricing seasons for a package.
- `get_package_by_slug(slug: str) -> Optional[Package]` - Retrieves a package using its SEO-friendly URL slug.

## 7. PackageDepartureRepository

- `get_available_departures(package_id: str, start_date: date, end_date: date) -> List[PackageDeparture]` - Finds open departures within a date range with `available_capacity > 0`.
- `decrement_capacity(departure_id: str, count: int, version_id: int) -> PackageDeparture` - Safely decrements capacity using Optimistic Locking (requires exact `version_id`).
- `increment_capacity(departure_id: str, count: int) -> PackageDeparture` - Restores capacity (e.g., upon booking cancellation).

## 8. PackageBookingRepository

- `get_package_booking_with_custom_itinerary(booking_id: str) -> Optional[PackageBooking]` - Retrieves a package booking alongside any related `CustomItinerary` and items.
- `get_upcoming_package_bookings(days_ahead: int) -> List[PackageBooking]` - Queries package bookings starting within a certain timeframe.

## 9. InvoiceRepository

- `generate_invoice_number() -> str` - Safely generates a sequential, unique invoice number.
- `get_unpaid_invoices_by_user(user_id: str) -> List[Invoice]` - Retrieves all pending invoices for a specific user.
- `find_invoice_by_subscription(subscription_id: str) -> List[Invoice]` - Fetches billing history for a corporate subscription.
- `mark_invoice_as_paid(invoice_id: str, payment_id: str) -> Invoice` - Updates invoice status and links the corresponding payment record.

## 10. PaymentRepository

- `log_payment_attempt(invoice_id: str, gateway: str, amount: float) -> Payment` - Creates a new payment record in 'PENDING' status.
- `update_payment_transaction(payment_id: str, transaction_id: str, status: PaymentStatus) -> Payment` - Records the success/failure from the gateway.
- `get_payments_by_invoice(invoice_id: str) -> List[Payment]` - Retrieves all payment attempts for an invoice.

## 11. PassengerRepository

- `bulk_insert_passengers(passengers: List[dict]) -> List[Passenger]` - Efficiently inserts multiple passenger records for a single booking.
- `get_passengers_for_booking(booking_id: str) -> List[Passenger]` - Retrieves all passengers associated with a booking.

## 12. ServiceFeeRepository

- `get_active_fee_rules_by_type(fee_type: FeeType) -> List[ServiceFeeRule]` - Fetches applicable rules (e.g., FLIGHT_BOOKING_FEE) ordered by priority.

## 13. AuditLogRepository

- `log_action(user_id: str, action: AuditAction, entity_type: EntityType, entity_id: str, changes: dict, ip_address: str) -> AuditLog` - Inserts a new security audit record.
- `get_entity_history(entity_type: EntityType, entity_id: str) -> List[AuditLog]` - Retrieves a chronological trail of changes for a specific entity.
- `get_recent_admin_actions(limit: int) -> List[AuditLog]` - Fetches the latest system mutations performed by administrators.

## 14. NotificationRepository

- `get_unread_notifications(user_id: str, limit: int) -> List[Notification]` - Retrieves prioritizing unread alerts for a user.
- `mark_as_read(notification_id: str) -> Notification` - Updates the read status of a specific notification.
- `mark_all_as_read_for_user(user_id: str) -> bool` - Bulk updates all notifications for a user.
- `get_notification_template(trigger_event: str) -> Optional[NotificationTemplate]` - Fetches the active template for a specific system event.

## 15. AnalyticsRepository

- `aggregate_metrics_by_date(metric_name: str, start_date: date, end_date: date) -> List[dict]` - Groups and sums analytics metrics over a time series.
- `increment_metric_counter(metric_name: str, date_dimension: date, category: str) -> AnalyticsMetric` - Upserts and increments a specific counter.
