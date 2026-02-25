# Service Level Functionality Report

This report evaluates the **Service Layer** evaluating business logic implementation, abstraction integrity, external boundaries, and correctness.

## 1. System Architecture & Context

- **Registry Pattern (`app/services/registry.py`)**: Well constructed. It mirrors the RepositoryRegistry to ensure controllers have a single, clean import point for interacting with business logic sequentially.
- **Good Inter-Service Composability**: `CompanyService.manage_employees` actively utilizes `AuthService.register_user` in order to maintain password hashing standards rather than re-inventing the wheel. This is great component reuse.
- **GDPR Compliance**: `UserService.delete_account` utilizes a soft-delete mechanism combined with cryptographic and PII blanking (`[DELETED_ACCOUNT]`, scrambling) to ensure privacy law adherences.

## 2. Abstraction Leakage & Architecture Violations

The most critical issue present across the entire Service layer is an egregious violation of the **Repository Pattern** boundaries. Services are actively importing `app.extensions.db` directly, and executing raw SQLAlchemy commands that should be natively handled by the Repositories.

- **Analytics Bypass (`app/services/analytics/service.py`)**: `AnalyticsService.track_event` bypasses `AnalyticsRepository.increment_metric_counter` (which handles concurrency locks safely). It uses `self.analytics_repo.model.query.filter_by` directly. Likewise, `generate_dashboard_report` builds manual queries instead of using the repo's native aggregation functions.
- **Audit Logging Bypass (`app/services/audit/service.py`)**: `record_critical_action` calls `self.audit_repo.create(...)` directly. By bypassing `self.audit_repo.log_action(...)`, the service entirely skips the `sanitize_audit_payload(changes)` function mapping, creating a **massive PII logging vulnerability**.
- **Package Encapsulation Broken (`app/services/package/service.py`)**: Both `search_packages` and `customize_itinerary` execute chained queries on `self.package_repo.model.query` directly and make explicit `db.session.add()` / `db.session.delete()` calls.
- **Flight Raw DB Commands (`app/services/flight/service.py`)**: `book_flight` bypasses `FlightBookingRepository` to add nested Flight segments manually via `db.session.add(seg)` and imports `db` inline.
- **Payment Encapsulation Broken (`app/services/payment/service.py`)**: `verify_payment` queries `self.invoice_repo.model.query.filter_by(...)` instead of abstracting the invoice query behind a repository method.

## 3. Logical & Correctness Bugs

- **Payment/Invoice Math (`app/services/payment/service.py`)**: In `generate_invoice`, the due date logic is fundamentally flawed: `due = datetime.now(timezone.utc).replace(day=min(issued.day + 7, 28)).date()`. If an invoice is issued on the 25th of the month, `25 + 7 = 32`. `min(32, 28) = 28`. Thus, an invoice issued on the 25th is made due in 3 days instead of 7. It will also completely crash across month boundaries natively.
- **Auth User Creation Brittle Pattern (`app/services/auth/service.py`)**: In `register_user`, a `User` model is instantiated to trigger `.set_password()`, but then its attributes are stripped dynamically via `__dict__` and handed to the DB connection to reconstruct entirely anew. This is brittle and risks ignoring nested SQLAlchemy `_sa_instance` states or failing schema cascades.

## 4. Production Readiness

Before this application can enter production, the immediate restructuring of the codebase is required:

1. **Remove `from app.extensions import db` from all `app/services/` logic.**
2. **Force all `.model.query` calls originating inside the Service layer directly into explicit Repository methods.**
3. **Patch the Payment due-date calculation to use appropriate `timedelta(days=7)` structures rather than literal string replacements.**
4. **Enforce `sanitize_audit_payload` usage for all auditing workflows natively.**

## 5. Next Steps

These findings, alongside the **Repository Level Report**, identify that while the business structure maps well against the Concierge constraints, the code organization has leaked constraints between the Data-Access and logic layers. Please review these logs to triage the next steps in stabilization.
