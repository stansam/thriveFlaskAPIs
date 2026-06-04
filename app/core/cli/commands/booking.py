import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_bookings

@click.command("seed-booking")
@with_appcontext
def seed_booking_command() -> None:
    """Seed Bookings (Car, Flight, Hotel, Package) and Flight Segments with sample data."""
    check_and_seed_bookings()
