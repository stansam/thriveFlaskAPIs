import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_packages

@click.command("seed-package-items")
@with_appcontext
def seed_package_items_command() -> None:
    """Seed PackageHighlight, PackageInclusion, and PackageItineraryDay tables with sample data."""
    check_and_seed_packages()
