import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import (
    check_and_seed_users,
    check_and_seed_corporate,
    check_and_seed_clients,
    check_and_seed_fee_schedules,
    check_and_seed_fees,
    check_and_seed_packages,
    check_and_seed_media,
    check_and_seed_bookings,
    check_and_seed_booking_passengers,
    check_and_seed_fee_snapshots,
    check_and_seed_payments,
    check_and_seed_referrals,
    check_and_seed_loyalty,
    check_and_seed_notification_templates,
    check_and_seed_notifications,
    check_and_seed_audits
)

@click.command("seed-db")
@with_appcontext
def seed_db_command() -> None:
    """Seed the entire database with comprehensive sample data (chains all individual seeders)."""
    click.echo("=== Starting Database Seeding ===")
    
    check_and_seed_users()
    check_and_seed_corporate()
    check_and_seed_clients()
    check_and_seed_fee_schedules()
    check_and_seed_fees()
    check_and_seed_packages()
    check_and_seed_media()
    check_and_seed_bookings()
    check_and_seed_booking_passengers()
    check_and_seed_fee_snapshots()
    check_and_seed_payments()
    check_and_seed_referrals()
    check_and_seed_loyalty()
    check_and_seed_notification_templates()
    check_and_seed_notifications()
    check_and_seed_audits()
    
    click.echo("=== Database Seeding Completed Successfully ===")
