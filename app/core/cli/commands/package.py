import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_packages

@click.command("seed-package")
@with_appcontext
def seed_package_command() -> None:
    """Seed TravelPackage and related sub-tables (highlights, inclusions, days, price tiers, insurance) with sample data."""
    check_and_seed_packages()
