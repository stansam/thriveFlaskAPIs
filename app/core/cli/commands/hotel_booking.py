import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_bookings

@click.command("seed-hotel-booking")
@with_appcontext
def seed_hotel_booking_command() -> None:
    """Seed HotelBooking table with sample data."""
    check_and_seed_bookings()
