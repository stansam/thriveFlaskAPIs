from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, TypeVar, cast
import click

from app.models.base import db
from app.models import (
    User, UserPreference, CorporateAccount, CorporateSubscription,
    Client, ClientPreference, ServiceFeeSchedule, ServiceFee,
    TravelPackage, PackageHighlight, PackageInclusion, PackageItineraryDay,
    PackagePriceTier, PackageInsurance, MediaAsset, PackageMedia,
    CarBooking, FlightBooking, FlightSegment, HotelBooking, PackageBooking,
    BookingPassenger, ServiceFeeSnapshot, Payment, Referral, LoyaltyLedger,
    NotificationTemplate, Notification, NotificationDelivery, AuditLog
)

from app.core.cli.data import (
    USERS, USER_PREFERENCES, CORPORATE_ACCOUNTS, CORPORATE_SUBSCRIPTIONS,
    CLIENTS, CLIENT_PREFERENCES, FEE_SCHEDULES, FEES, TRAVEL_PACKAGES,
    PACKAGE_HIGHLIGHTS, PACKAGE_INCLUSIONS, PACKAGE_ITINERARY_DAYS,
    PACKAGE_PRICE_TIERS, PACKAGE_INSURANCES, MEDIA_ASSETS, PACKAGE_MEDIA_ITEMS,
    CAR_BOOKINGS, FLIGHT_BOOKINGS, FLIGHT_SEGMENTS, HOTEL_BOOKINGS,
    PACKAGE_BOOKINGS, BOOKING_PASSENGERS, FEE_SNAPSHOTS, PAYMENTS,
    REFERRALS, LOYALTY_ENTRIES, NOTIFICATION_TEMPLATES, NOTIFICATIONS,
    NOTIFICATIONS_DELIVERIES, AUDITS
)

def check_and_seed_users(actor_id: str | None = None) -> None:
    """Ensure Users and UserPreferences are seeded."""
    if db.session.query(User).count() == 0:
        click.echo("Seeding Users and User Preferences...")
        for user_data in USERS:
            user = User(**user_data)
            db.session.add(user)
        for pref_data in USER_PREFERENCES:
            pref = UserPreference(**pref_data)
            db.session.add(pref)
        db.session.commit()
        click.echo("Users and User Preferences seeded successfully.")

def check_and_seed_corporate(actor_id: str | None = None) -> None:
    """Ensure Corporate Accounts and Subscriptions are seeded."""
    if db.session.query(CorporateAccount).count() == 0:
        click.echo("Seeding Corporate Accounts and Subscriptions...")
        for acc_data in CORPORATE_ACCOUNTS:
            acc = CorporateAccount(**acc_data)
            db.session.add(acc)
        for sub_data in CORPORATE_SUBSCRIPTIONS:
            sub = CorporateSubscription(**sub_data)
            db.session.add(sub)
        db.session.commit()
        click.echo("Corporate Accounts and Subscriptions seeded successfully.")

def check_and_seed_clients(actor_id: str | None = None) -> None:
    """Ensure Clients and ClientPreferences are seeded. Depends on Corporate Accounts."""
    if db.session.query(Client).count() == 0:
        check_and_seed_corporate(actor_id)
        click.echo("Seeding Clients and Client Preferences...")
        for client_data in CLIENTS:
            client = Client(**client_data)
            db.session.add(client)
        for pref_data in CLIENT_PREFERENCES:
            pref = ClientPreference(**pref_data)
            db.session.add(pref)
        db.session.commit()
        click.echo("Clients and Client Preferences seeded successfully.")

def check_and_seed_fee_schedules(actor_id: str | None = None) -> None:
    """Ensure Service Fee Schedules are seeded."""
    if db.session.query(ServiceFeeSchedule).count() == 0:
        click.echo("Seeding Service Fee Schedules...")
        for schedule_data in FEE_SCHEDULES:
            schedule = ServiceFeeSchedule(**schedule_data)
            db.session.add(schedule)
        db.session.commit()
        click.echo("Service Fee Schedules seeded successfully.")

def check_and_seed_fees(actor_id: str | None = None) -> None:
    """Ensure Service Fees are seeded. Depends on Fee Schedules."""
    if db.session.query(ServiceFee).count() == 0:
        check_and_seed_fee_schedules(actor_id)
        click.echo("Seeding Service Fees...")
        for fee_data in FEES:
            fee = ServiceFee(**fee_data)
            db.session.add(fee)
        db.session.commit()
        click.echo("Service Fees seeded successfully.")

def check_and_seed_packages(actor_id: str | None = None) -> None:
    """Ensure Travel Packages, highlights, inclusions, itinerary days, price tiers, insurance options are seeded."""
    if db.session.query(TravelPackage).count() == 0:
        click.echo("Seeding Travel Packages, Highlights, Inclusions, Itinerary Days, Price Tiers, and Insurance Options...")
        for pkg_data in TRAVEL_PACKAGES:
            pkg = TravelPackage(**pkg_data)
            db.session.add(pkg)
        for hl_data in PACKAGE_HIGHLIGHTS:
            hl = PackageHighlight(**hl_data)
            db.session.add(hl)
        for inc_data in PACKAGE_INCLUSIONS:
            inc = PackageInclusion(**inc_data)
            db.session.add(inc)
        for day_data in PACKAGE_ITINERARY_DAYS:
            day = PackageItineraryDay(**day_data)
            db.session.add(day)
        for tier_data in PACKAGE_PRICE_TIERS:
            tier = PackagePriceTier(**tier_data)
            db.session.add(tier)
        for ins_data in PACKAGE_INSURANCES:
            ins = PackageInsurance(**ins_data)
            db.session.add(ins)
        db.session.commit()
        click.echo("Travel Packages and child tables seeded successfully.")

def check_and_seed_media(actor_id: str | None = None) -> None:
    """Ensure Media Assets and Package Media links are seeded. Depends on Packages."""
    if db.session.query(MediaAsset).count() == 0:
        check_and_seed_packages(actor_id)
        click.echo("Seeding Media Assets and Package Media Junctions...")
        for media_data in MEDIA_ASSETS:
            media = MediaAsset(**media_data)
            db.session.add(media)
        # Flush so media asset primary keys are resolved in DB before linking
        db.session.flush()
        for link_data in PACKAGE_MEDIA_ITEMS:
            link = PackageMedia(**link_data)
            db.session.add(link)
        db.session.commit()
        click.echo("Media Assets seeded successfully.")

def check_and_seed_bookings(actor_id: str | None = None) -> None:
    """Ensure Bookings (Car, Flight, Hotel, Package) and Flight Segments are seeded. Depends on Clients and Packages."""
    # We check if FlightBooking exists as a proxy for bookings
    if db.session.query(FlightBooking).count() == 0:
        check_and_seed_clients(actor_id)
        check_and_seed_packages(actor_id)
        click.echo("Seeding Bookings (Car, Hotel, Flight, Package) and Flight Segments...")
        for car_data in CAR_BOOKINGS:
            car = CarBooking(**car_data)
            db.session.add(car)
        for hotel_data in HOTEL_BOOKINGS:
            hotel = HotelBooking(**hotel_data)
            db.session.add(hotel)
        for flight_data in FLIGHT_BOOKINGS:
            flight = FlightBooking(**flight_data)
            db.session.add(flight)
        db.session.flush()
        for segment_data in FLIGHT_SEGMENTS:
            segment = FlightSegment(**segment_data)
            db.session.add(segment)
        for pkg_booking_data in PACKAGE_BOOKINGS:
            pkg_b = PackageBooking(**pkg_booking_data)
            db.session.add(pkg_b)
        db.session.commit()
        click.echo("Bookings and flight segments seeded successfully.")

def check_and_seed_booking_passengers(actor_id: str | None = None) -> None:
    """Ensure Booking Passengers are seeded. Depends on Bookings."""
    if db.session.query(BookingPassenger).count() == 0:
        check_and_seed_bookings(actor_id)
        click.echo("Seeding Booking Passengers...")
        for passenger_data in BOOKING_PASSENGERS:
            passenger = BookingPassenger(**passenger_data)
            db.session.add(passenger)
        db.session.commit()
        click.echo("Booking Passengers seeded successfully.")

def check_and_seed_fee_snapshots(actor_id: str | None = None) -> None:
    """Ensure Service Fee Snapshots are seeded. Depends on Bookings and Fees."""
    if db.session.query(ServiceFeeSnapshot).count() == 0:
        check_and_seed_bookings(actor_id)
        check_and_seed_fees(actor_id)
        click.echo("Seeding Service Fee Snapshots...")
        for snapshot_data in FEE_SNAPSHOTS:
            snapshot = ServiceFeeSnapshot(**snapshot_data)
            db.session.add(snapshot)
        db.session.commit()
        click.echo("Service Fee Snapshots seeded successfully.")

def check_and_seed_payments(actor_id: str | None = None) -> None:
    """Ensure Payments are seeded. Depends on Bookings."""
    if db.session.query(Payment).count() == 0:
        check_and_seed_bookings(actor_id)
        click.echo("Seeding Payments...")
        for payment_data in PAYMENTS:
            payment = Payment(**payment_data)
            db.session.add(payment)
        db.session.commit()
        click.echo("Payments seeded successfully.")

def check_and_seed_referrals(actor_id: str | None = None) -> None:
    """Ensure Referrals are seeded. Depends on Clients and Bookings."""
    if db.session.query(Referral).count() == 0:
        check_and_seed_clients(actor_id)
        check_and_seed_bookings(actor_id)
        click.echo("Seeding Referrals...")
        for ref_data in REFERRALS:
            ref = Referral(**ref_data)
            db.session.add(ref)
        db.session.commit()
        click.echo("Referrals seeded successfully.")

def check_and_seed_loyalty(actor_id: str | None = None) -> None:
    """Ensure Loyalty ledger entries are seeded. Depends on Clients, Bookings, and Referrals."""
    if db.session.query(LoyaltyLedger).count() == 0:
        check_and_seed_clients(actor_id)
        check_and_seed_bookings(actor_id)
        check_and_seed_referrals(actor_id)
        click.echo("Seeding Loyalty Ledger...")
        for loyalty_data in LOYALTY_ENTRIES:
            entry = LoyaltyLedger(**loyalty_data)
            db.session.add(entry)
        db.session.commit()
        click.echo("Loyalty Ledger seeded successfully.")

def check_and_seed_notification_templates(actor_id: str | None = None) -> None:
    """Ensure Notification Templates are seeded."""
    if db.session.query(NotificationTemplate).count() == 0:
        click.echo("Seeding Notification Templates...")
        for template_data in NOTIFICATION_TEMPLATES:
            template = NotificationTemplate(**template_data)
            db.session.add(template)
        db.session.commit()
        click.echo("Notification Templates seeded successfully.")

def check_and_seed_notifications(actor_id: str | None = None) -> None:
    """Ensure Notifications and Notification Deliveries are seeded. Depends on Templates, Clients, Users."""
    if db.session.query(Notification).count() == 0:
        check_and_seed_notification_templates(actor_id)
        check_and_seed_clients(actor_id)
        check_and_seed_users(actor_id)
        click.echo("Seeding Notifications and Deliveries...")
        for notif_data in NOTIFICATIONS:
            notif = Notification(**notif_data)
            db.session.add(notif)
        db.session.flush()
        for delivery_data in NOTIFICATIONS_DELIVERIES:
            delivery = NotificationDelivery(**delivery_data)
            db.session.add(delivery)
        db.session.commit()
        click.echo("Notifications and Deliveries seeded successfully.")

def check_and_seed_audits(actor_id: str | None = None) -> None:
    """Ensure Audit Logs are seeded. Depends on Users."""
    if db.session.query(AuditLog).count() == 0:
        check_and_seed_users(actor_id)
        click.echo("Seeding Audit Logs...")
        for audit_data in AUDITS:
            audit = AuditLog(**audit_data)
            db.session.add(audit)
        db.session.commit()
        click.echo("Audit Logs seeded successfully.")
