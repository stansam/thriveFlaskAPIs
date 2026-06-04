import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_bookings

@click.command("seed-package-booking")
@with_appcontext
def seed_package_booking_command() -> None:
    """Seed PackageBooking table with sample data."""
    check_and_seed_bookings()
