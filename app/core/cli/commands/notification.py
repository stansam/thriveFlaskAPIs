import click
from flask.cli import with_appcontext
from app.core.cli.commands.utils import check_and_seed_notifications

@click.command("seed-notification")
@with_appcontext
def seed_notification_command() -> None:
    """Seed Notifications, Deliveries and templates with sample data."""
    check_and_seed_notifications()
