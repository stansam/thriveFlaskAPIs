import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_clients

@click.command("seed-client-preference")
@with_appcontext
def seed_client_preference_command() -> None:
    """Seed ClientPreference table with sample data."""
    check_and_seed_clients()
