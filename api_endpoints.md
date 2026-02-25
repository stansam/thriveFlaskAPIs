# Thrive Global Travel: Comprehensive API Endpoints Architecture

This document serves as the master blueprint detailing **all API endpoints** required to operate the Thrive Global Travel backend based on the business requirements (B2B SaaS, Offline Manual Payments, GDS Integrations, and 24/7 Concierge).

---

## 1. Auth APIs (`/api/auth`)
Handles authentication, identity validation, and security loops for all user types.

| Endpoint | Method | Description | Notifications & Comms | Sockets | Analytics | Audit Logging |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/login` | `POST` | Exchange Email/PW for Session/JWT. | `[EMAIL] Suspicious Login (if new IP)` | - | `login_success`, `login_failed` | Log `LOGIN_SUCCESS` / `LOGIN_FAILED` |
| `/register` | `POST` | Core user registration (B2C & Employees). | `[EMAIL] Account Verification Link` | - | `user_registered` | Log `ACCOUNT_CREATED` |
| `/verify-email` | `POST` | Consume secure crypto token from email. | `[EMAIL] Welcome to Thrive` | - | `email_verified` | Log `EMAIL_VERIFIED` |
| `/forgot-password` | `POST` | Issue password reset crypto token. | `[EMAIL] Password Reset Link` | - | `password_reset_requested` | - |
| `/reset-password` | `POST` | Consume token and set new password. | `[EMAIL] Password Reset Confirm` | - | `password_reset_completed`| Log `PASSWORD_CHANGED` |
| `/logout` | `POST` | Terminate active tokens/sessions. | - | `disconnect` | `user_logged_out` | Log `LOGOUT` |
| `/oauth/google` | `GET` | Initiate Google SSO flow. | - | - | `oauth_initiated` | - |
| `/oauth/callback`| `POST` | Finalize mapped identity from Google. | `[EMAIL] Welcome (if new)` | - | `oauth_completed` | Log `ACCOUNT_CREATED_OAUTH`|

---

## 2. Main APIs (`/api/public`)
Unauthenticated endpoints designed for marketing, SEO, and top-of-funnel conversions.

| Endpoint | Method | Description | Notifications & Comms | Sockets | Analytics | Audit Logging |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/flights/search` | `GET` | Proxy to GDS searching available segments. | - | `live_pricing_stream` | `flight_search_performed` | - |
| `/packages` | `GET` | List available Tour Packages, filterable. | - | - | `package_catalog_viewed` | - |
| `/packages/{slug}`| `GET` | Fetch specific Package/Itinerary details. | - | - | `package_detail_viewed` | - |
| `/departures` | `GET` | List upcoming departures/Slot availability.| - | - | `departure_slots_viewed` | - |
| `/pricing-tiers` | `GET` | Fetch active B2B / SaaS subscription rules.| - | - | `pricing_viewed` | - |
| `/contact` | `POST` | Submit general inquiries/lead gen. | `[EMAIL] Thank you / [ADMIN_EMAIL] New Lead` | - | `contact_form_submitted` | - |

---

## 3. Admin APIs (`/api/admin`)
Secured routes requiring `UserRole.ADMIN` globally. Powers the internal back-office.

| Endpoint | Method | Description | Notifications & Comms | Sockets | Analytics | Audit Logging |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/dashboard` | `GET` | Fetch system-wide aggregations/revenue. | - | `live_revenue_bump` | - | - |
| `/payments/verify` | `POST` | Reconcile offline wire transfers natively. | `[EMAIL] Payment Confirmed` | - | `payment_reconciled` | Log `PAYMENT_VERIFIED` (Critical) |
| `/bookings/{id}/ticket`| `POST`| Generate/Attach PDF Flight eTickets. | `[EMAIL] Your E-Tickets are Ready`| `ticket_ready` | `eticket_issued` | Log `ETICKET_ISSUED` (Critical) |
| `/bookings/{id}/void`| `POST` | Force cancel a booking/refund process. | `[EMAIL] Booking Cancelled` | - | `booking_voided` | Log `BOOKING_VOIDED` (Critical) |
| `/companies` | `GET` | List all registered B2B entities. | - | - | - | - |
| `/companies/{id}/status`| `PUT`| Suspend/Activate a corporate account. | `[EMAIL] Enterprise Account Status` | - | `company_status_changed` | Log `COMPANY_SUSPENDED` (Critical) |
| `/packages/manage` | `POST` | Create/Edit holiday Packages & rules. | - | - | `package_modified` | Log `PACKAGE_CREATED` |
| `/fees` | `POST`| Manage explicit ServiceFee rule layers. | - | - | `service_fee_updated` | Log `FEE_RULE_MODIFIED` (Critical) |
| `/audit` | `GET` | Tail system-wide compliance logs. | - | - | - | Log `AUDIT_LOGS_VIEWED` |

---

## 4. Client APIs (`/api/client`)
Secured routes for standard authenticated users to manage their profiles, bookings, and corporate seats.

| Endpoint | Method | Description | Notifications & Comms | Sockets | Analytics | Audit Logging |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/profile` | `GET/PUT` | Manage identity and physical traits. | - | - | `profile_updated` | Log `PROFILE_UPDATED` |
| `/preferences` | `PUT` | Update notification and currency toggles.| - | - | `preferences_updated` | - |
| `/bookings` | `GET` | List user history / upcoming trips. | - | - | `user_bookings_viewed` | - |
| `/flight/book` | `POST` | Initiate flight transaction / checkout. | `[EMAIL] Pending Booking / Invoice Generated`| - | `flight_booking_initiated`| Log `BOOKING_CREATED` |
| `/package/book` | `POST` | Initiate package transaction & passenger dump.| `[EMAIL] Pending Booking / Invoice Generated`| - | `package_booking_initiated`| Log `BOOKING_CREATED` |
| `/booking/{id}/passengers`| `POST`| Bulk upload traveler Passport manifests. | - | - | `group_passengers_added`| Log `PASSENGERS_ATTACHED` |
| `/invoice/{num}/pay` | `POST` | Submit Bank Transfer receipt (Proof URL). | `[EMAIL] Receipt Received (Pending Admin)` | - | `payment_proof_submitted` | Log `PAYMENT_PROOF_SUBMITTED` |
| `/company/employees` | `POST` | (B2B Admin) Invite new staff members. | `[EMAIL] Corporate Invite Link` | - | `b2b_employee_invited` | Log `EMPLOYEE_ADDED` |
| `/company/employees/{id}`| `DELETE`| (B2B Admin) Soft-sever employee bindings. | `[EMAIL] Access Revoked` | - | `b2b_employee_removed` | Log `EMPLOYEE_REMOVED` |
| `/subscription/upgrade`| `POST` | Upgrade corporate tier natively. | `[EMAIL] Subscription Level Bumped` | - | `subscription_upgraded` | Log `SUBSCRIPTION_CHANGED`|
| `/account/delete` | `DELETE`| (GDPR) Fire irreversible account wiping. | `[EMAIL] Farewell/Data Removed` | - | `account_deleted` | Log `ACCOUNT_DELETED` (Critical)|
