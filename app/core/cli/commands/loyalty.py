import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_loyalty

@click.command("seed-loyalty")
@with_appcontext
def seed_loyalty_command() -> None:
    """Seed LoyaltyLedger table with sample data."""
    check_and_seed_loyalty()
