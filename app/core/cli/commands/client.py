import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_clients

@click.command("seed-client")
@with_appcontext
def seed_client_command() -> None:
    """Seed Client and ClientPreference tables with sample data."""
    check_and_seed_clients()
