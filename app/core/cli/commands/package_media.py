import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_media

@click.command("seed-package-media")
@with_appcontext
def seed_package_media_command() -> None:
    """Seed PackageMedia table with sample data."""
    check_and_seed_media()
