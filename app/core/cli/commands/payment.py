import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_payments

@click.command("seed-payment")
@with_appcontext
def seed_payment_command() -> None:
    """Seed Payment table with sample data."""
    check_and_seed_payments()
