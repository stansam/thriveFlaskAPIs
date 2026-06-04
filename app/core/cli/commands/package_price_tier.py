import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_packages

@click.command("seed-package-price-tier")
@with_appcontext
def seed_package_price_tier_command() -> None:
    """Seed PackagePriceTier table with sample data."""
    check_and_seed_packages()
