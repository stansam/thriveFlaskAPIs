import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_bookings

@click.command("seed-car-booking")
@with_appcontext
def seed_car_booking_command() -> None:
    """Seed CarBooking table with sample data."""
    check_and_seed_bookings()
