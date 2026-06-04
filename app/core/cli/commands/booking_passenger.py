import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_booking_passengers

@click.command("seed-booking-passenger")
@with_appcontext
def seed_booking_passenger_command() -> None:
    """Seed BookingPassenger table with sample data."""
    check_and_seed_booking_passengers()
