import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_users

@click.command("seed-user")
@with_appcontext
def seed_user_command() -> None:
    """Seed User and UserPreference tables with sample data."""
    check_and_seed_users()
