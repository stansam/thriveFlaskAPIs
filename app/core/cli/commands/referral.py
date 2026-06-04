import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_referrals

@click.command("seed-referral")
@with_appcontext
def seed_referral_command() -> None:
    """Seed Referral table with sample data."""
    check_and_seed_referrals()
