# Thrive CLI Toolset

This directory contains the custom Flask CLI commands, seed data, and utilities built for database seeding, maintenance, and diagnostics within the Thrive Backend application.

## Directory Structure

*   [commands/](file:///home/vault/Documents/thriveBundle/thriveBackend/app/core/cli/commands/): The Click command definitions registered dynamically within the Flask application.
*   [data/](file:///home/vault/Documents/thriveBundle/thriveBackend/app/core/cli/data/): Modular Python datasets populated with sample inputs for all 27+ models.

All CLI commands are dynamically registered via [app/core/register/cli.py](file:///home/vault/Documents/thriveBundle/thriveBackend/app/core/register/cli.py).

---

## 1. Global & Modular Database Seeding

We support seeding the entire database in topological dependency order, or individual tables independently with built-in dependency resolution.

### Global Database Seeding

*   **Command**: `flask seed-db` (legacy alias: `flask db-seed`)
*   **Description**: Run this command to completely seed the database from an empty state. It executes all individual seeders in the correct order to guarantee foreign key constraint satisfaction.
*   **Implementation**: Defined in [app/core/cli/commands/seed_db.py](file:///home/vault/Documents/thriveBundle/thriveBackend/app/core/cli/commands/seed_db.py).

### Individual Table Seeders

Each seeder can be run independently using the commands listed below. 

> [!NOTE]
> **Self-Healing Architecture**
>
> If you run an individual seeder (e.g. `flask seed-payment`) and its dependencies do not exist (e.g. no Users or Bookings), the system's checker defined in [utils.py](file:///home/vault/Documents/thriveBundle/thriveBackend/app/core/cli/commands/utils.py) will automatically execute the parent seeders first to ensure relational integrity before seeding the target table.

| CLI Command | Target Model(s) / Tables | Dependency Chain |
| :--- | :--- | :--- |
| `flask seed-user` | `User`, `UserPreference` | None |
| `flask seed-user-preference` | `UserPreference` | `User` |
| `flask seed-corporate` | `CorporateAccount`, `CorporateSubscription` | None |
| `flask seed-client` | `Client`, `ClientPreference` | None |
| `flask seed-client-preference` | `ClientPreference` | `Client` |
| `flask seed-fee-schedule` | `ServiceFeeSchedule` | None |
| `flask seed-fee` | `ServiceFee`, `ServiceFeeSchedule` | `ServiceFeeSchedule` |
| `flask seed-media` | `MediaAsset` | None |
| `flask seed-package` | `TravelPackage`, `PackageHighlight`, `PackageInclusion`, `PackageItineraryDay`, `PackagePriceTier`, `PackageInsurance` | None |
| `flask seed-package-items` | `PackageHighlight`, `PackageInclusion`, `PackageItineraryDay` | `TravelPackage` |
| `flask seed-package-media` | `PackageMedia` (junction table) | `TravelPackage`, `MediaAsset` |
| `flask seed-package-price-tier` | `PackagePriceTier` | `TravelPackage` |
| `flask seed-package-insurance` | `PackageInsurance` | `TravelPackage` |
| `flask seed-booking` | `Booking` subclasses (Car, Flight, Hotel, Package) | `Client`, `User`, `TravelPackage` (for pkg bookings) |
| `flask seed-car-booking` | `CarBooking` | `Client`, `User` |
| `flask seed-flight-booking` | `FlightBooking`, `FlightSegment` | `Client`, `User` |
| `flask seed-hotel-booking` | `HotelBooking` | `Client`, `User` |
| `flask seed-package-booking` | `PackageBooking` | `Client`, `User`, `TravelPackage`, `PackagePriceTier` |
| `flask seed-booking-passenger` | `BookingPassenger` | `Booking` subclasses |
| `flask seed-fee-snapshot` | `ServiceFeeSnapshot` | `Booking` subclasses, `ServiceFee` |
| `flask seed-payment` | `Payment` | `Booking` subclasses |
| `flask seed-referral` | `Referral` | `Client` |
| `flask seed-loyalty` | `LoyaltyLedger` | `Client` |
| `flask seed-notification-template` | `NotificationTemplate` | None |
| `flask seed-notification` | `Notification`, `NotificationDelivery` | `User`, `NotificationTemplate` |
| `flask seed-notification-delivery` | `NotificationDelivery` | `Notification` |
| `flask seed-audit` | `AuditLog` | `User` |

---

## 2. Table Management & Maintenance

*   **Command**: `flask manage-tables [OPTIONS]`
*   **Description**: A powerful diagnostics and cleanup utility.
*   **Implementation**: Defined in [app/core/cli/commands/manage_tables.py](file:///home/vault/Documents/thriveBundle/thriveBackend/app/core/cli/commands/manage_tables.py).

### Options

*   `--list`: Prints a formatted table listing all database tables along with their current row counts.
*   `--empty <tables>`: Deletes all rows from specific tables (comma-separated list of table names, or `all` to empty all tables).
*   `--drop <tables>`: Drops tables (comma-separated list of table names, or `all` to drop all tables).
*   `--force`: Bypasses confirmation prompts.

> [!WARNING]
> **Environment Guardrails**
>
> Destructive actions (`--empty` and `--drop`) are strictly restricted to `development` and `testing` environments (read from `FLASK_ENV`). They will be aborted instantly if run in `production`.
>
> SQLite foreign key constraints are temporarily disabled (`PRAGMA foreign_keys = OFF`) during delete and drop sequences to prevent cascading failures.

---

## 3. Other Core CLI Commands

### Create Admin
*   **Command**: `flask create-admin`
*   **Description**: Prompts interactively for credentials to register the initial super-admin user in the database.
*   **Implementation**: [app/core/cli/commands/create_admin.py](file:///home/vault/Documents/thriveBundle/thriveBackend/app/core/cli/commands/create_admin.py).

### List Routes
*   **Command**: `flask routes`
*   **Description**: Lists all registered application endpoints/routes, HTTP methods, and their associated view functions.
*   **Implementation**: [app/core/cli/commands/routes.py](file:///home/vault/Documents/thriveBundle/thriveBackend/app/core/cli/commands/routes.py).

### Rotate MFA Keys
*   **Command**: `flask rotate-mfa-keys`
*   **Description**: Decrypts user MFA totp keys with the old environment key and re-encrypts them using the new environment key.
*   **Implementation**: [app/core/cli/commands/rotate_mfa_keys.py](file:///home/vault/Documents/thriveBundle/thriveBackend/app/core/cli/commands/rotate_mfa_keys.py).

---

## Usage Examples

### 1. View Current Database Row Counts
```bash
flask manage-tables --list
```

### 2. Seed the Entire Database
```bash
flask seed-db
```

### 3. Clear all tables and Re-Seed
```bash
flask manage-tables --empty all --force
flask seed-db
```

### 4. Seed a single table (e.g., user preferences)
*If users are not seeded yet, the command will automatically seed users first, then seed user preferences.*
```bash
flask seed-user-preference
```
