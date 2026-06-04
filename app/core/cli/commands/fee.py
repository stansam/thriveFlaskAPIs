import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_fees

@click.command("seed-fee")
@with_appcontext
def seed_fee_command() -> None:
    """Seed ServiceFee and ServiceFeeSchedule tables with sample data."""
    check_and_seed_fees()
