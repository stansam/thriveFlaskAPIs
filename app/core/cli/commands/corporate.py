import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_corporate

@click.command("seed-corporate")
@with_appcontext
def seed_corporate_command() -> None:
    """Seed CorporateAccount and CorporateSubscription tables with sample data."""
    check_and_seed_corporate()
