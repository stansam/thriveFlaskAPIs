import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_packages

@click.command("seed-package-insurance")
@with_appcontext
def seed_package_insurance_command() -> None:
    """Seed PackageInsurance table with sample data."""
    check_and_seed_packages()
