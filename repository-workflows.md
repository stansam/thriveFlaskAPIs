# Repository Workflows

This document outlines the exhaustive list of custom repository (DB) level class-based functions required for the full completion of the professional, enterprise-level web app backend. These functions abstract away direct SQLAlchemy queries from the service layer.

## core/base

- `BaseRepository.create(entity)`
- `BaseRepository.get_by_id(id)`
- `BaseRepository.update(entity)`
- `BaseRepository.delete(id, soft=True)`
- `BaseRepository.get_all(pagination, filters)`

## user & company

- `UserRepository.get_by_email(email)`
- `UserRepository.get_by_referral_code(code)`
- `UserRepository.get_company_employees(company_id)`
- `UserRepository.update_last_login(user_id)`
- `CompanyRepository.get_by_tax_id(tax_id)`
- `CompanyRepository.get_active_companies()`
- `UserPreferenceRepository.get_by_user_id(user_id)`
- `UserPreferenceRepository.upsert(user_id, preferences_dict)`

## subscriptions & invoicing

- `SubscriptionPlanRepository.get_active_plans()`
- `SubscriptionPlanRepository.get_by_tier(tier_enum)`
- `UserSubscriptionRepository.get_active_subscription_by_user(user_id)`
- `UserSubscriptionRepository.get_active_subscription_by_company(company_id)`
- `UserSubscriptionRepository.increment_bookings_used(subscription_id)`
- `UserSubscriptionRepository.update_status(subscription_id, status)`
- `InvoiceRepository.get_by_invoice_number(invoice_number)`
- `InvoiceRepository.get_user_invoices(user_id, status)`
- `InvoiceRepository.get_company_invoices(company_id, status)`

## booking & passengers

- `BookingRepository.get_by_reference_code(reference_code)`
- `BookingRepository.get_user_bookings(user_id, status)`
- `BookingRepository.update_status(booking_id, status)`
- `BookingRepository.get_bookings_by_date_range(start_date, end_date)`
- `PassengerRepository.create_bulk(passengers_list)`
- `PassengerRepository.get_by_booking_id(booking_id)`

## flights

- `FlightBookingRepository.get_by_booking_id(booking_id)`
- `FlightBookingRepository.get_by_pnr(pnr)`
- `FlightRepository.create_bulk(flights_list)`
- `FlightRepository.get_by_flight_booking_id(flight_booking_id)`

## packages & availability

- `PackageRepository.get_by_slug(slug)`
- `PackageRepository.get_active_packages()`
- `PackageRepository.get_featured_packages()`
- `PackageItineraryRepository.get_by_package_id(package_id)`
- `PackageInclusionRepository.get_by_package_id(package_id)`
- `PackageMediaRepository.get_featured_images_by_package(package_id)`
- `PackagePricingSeasonRepository.get_active_season(package_id, target_date)`
- `PackagePricingRepository.get_pricing_by_season(season_id)`
- `PackageDepartureRepository.get_upcoming_departures(package_id)`
- `PackageDepartureRepository.decrement_capacity(departure_id, count, expected_version)` _(Uses optimistic locking)_
- `PackageDepartureRepository.update_status(departure_id, status)`

## custom itineraries

- `PackageBookingRepository.get_by_booking_id(booking_id)`
- `CustomItineraryRepository.get_by_package_booking_id(package_booking_id)`
- `CustomItineraryItemRepository.create_bulk(items_list)`
- `CustomItineraryItemRepository.get_by_itinerary_id(itinerary_id)`

## payments & fees

- `PaymentRepository.get_by_booking_id(booking_id)`
- `PaymentRepository.get_by_transaction_id(transaction_id)`
- `PaymentRepository.get_pending_manual_payments()`
- `PaymentRepository.update_status(payment_id, status)`
- `ServiceFeeRuleRepository.get_active_rules_by_type(fee_type)`
- `ServiceFeeRuleRepository.get_all_active_sorted_by_priority()`

## platform operations

- `NotificationRepository.get_unread_by_user(user_id)`
- `NotificationRepository.mark_as_read(notification_id)`
- `NotificationTemplateRepository.get_by_trigger_event(trigger_event)`
- `AuditLogRepository.log_action(user_id, action, entity_type, entity_id, changes_json)`
- `AuditLogRepository.get_entity_history(entity_type, entity_id)`
- `AnalyticsMetricRepository.increment_metric(metric_name, date, value_to_add)`
- `AnalyticsMetricRepository.get_metrics_by_date_range(start_date, end_date, category)`
