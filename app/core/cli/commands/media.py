import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_media

@click.command("seed-media")
@with_appcontext
def seed_media_command() -> None:
    """Seed MediaAsset and PackageMedia tables with sample data."""
    check_and_seed_media()
