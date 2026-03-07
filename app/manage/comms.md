# Thrive Travel - Models Requiring Sample Data

Based on the system requirements and existing schemas, the following models require sample data for testing and initial system seeding.

## 1. User & Access Models

- **User** (`app/models/user.py`): Test accounts for different roles (Admin, Client, Staff).
- **UserPreference** (`app/models/user_preference.py`): Associated preferences for the generated test users.
- **Company** (`app/models/company.py`): Corporate entities for B2B testing.

## 2. Subscription & Pricing Models

- **SubscriptionPlan** (`app/models/payment.py`): Standard plans based on context (Bronze - $150, Silver - $300, Gold - $500).
- **ServiceFeeRule** (`app/models/service_fee.py`): Default markup and fees (Domestic Flight, International Flight, Last-Minute, Group bookings, etc.).

## 3. Catalog & Operations Models

- **Service** (`app/models/services.py`): Core services offered (Airline ticket booking, Hotel bookings, Car rentals, Itinerary planning, Travel consultation).
- **Package** (`app/models/package.py`): Pre-defined travel packages (e.g., Dubai Luxury Escape).
- **PackageItinerary** (`app/models/package.py`): Daily schedules for the sample packages.
- **PackageInclusion** (`app/models/package.py`): Items included/excluded in the sample packages.
- **PackageMedia** (`app/models/package.py`): Sample image associations for the packages.

## Manage Command Breakdown

The data seeding will be handled by the following individual Flask CLI commands within the `manage` blueprint:

1. `create_testusers.py`: Generate standard client accounts and a test company.
2. `create_services.py`: Load the default dictionary of services.
3. `create_packages.py`: Load the catalog packages and their itineraries/inclusions.
4. `create_plans.py`: Create the Corporate Monthly subscription tiers.
5. `create_service_fees.py`: Load the dynamic fee rules for bookings.
6. `create_superuser.py`: (Already exists) For on-demand Admin account creation.
7. **`seed_database.py`**: A master command that invokes all of the above commands sequentially to completely populate an empty database.
