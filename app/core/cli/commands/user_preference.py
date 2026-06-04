import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_users

@click.command("seed-user-preference")
@with_appcontext
def seed_user_preference_command() -> None:
    """Seed UserPreference table with sample data."""
    check_and_seed_users()
